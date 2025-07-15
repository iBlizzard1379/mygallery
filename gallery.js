import * as THREE from 'three';
import { PointerLockControls } from 'three/addons/controls/PointerLockControls.js';

// 全局状态变量
let isViewingResource = false;
let currentResource = null;
let viewerContainer = null;
let downloadButton = null;
let closeButton = null;
let currentFilePath = null;
let currentFileType = null;
let originalCameraPosition = null;
let blurOverlay = null;
let raycaster = null;
let mouse = null;
let clickableObjects = [];
let controls = null;
let camera = null;
let lastCameraRotation = null;
let scene = null;
let renderer = null;
let materials = null;
// 移动控制变量
let velocity = new THREE.Vector3();
let direction = new THREE.Vector3();
let moveForward = false;
let moveBackward = false;
let moveLeft = false;
let moveRight = false;

// 调试功能
const debugDiv = document.getElementById('debug');
function log(message) {
    console.log(message);
    const p = document.createElement('p');
    p.textContent = message;
    if (debugDiv) {
        debugDiv.appendChild(p);
        // 保持滚动到底部
        debugDiv.scrollTop = debugDiv.scrollHeight;
    }
}

// 全局错误处理
window.addEventListener('error', function(event) {
    log(`全局错误: ${event.message} at ${event.filename}:${event.lineno}`);
    document.getElementById('loading').textContent = `加载出错: ${event.message}`;
    document.getElementById('loading').style.backgroundColor = 'rgba(255,0,0,0.7)';
    return false;
});

// 画廊常量
const GALLERY_LENGTH = 40;
const GALLERY_WIDTH = 6;
const GALLERY_HEIGHT = 4;
const WALL_THICKNESS = 0.5;
const FRAME_SPACING = 7;
const FRAME_WIDTH = 2;
const FRAME_HEIGHT = 1.5;
const FRAME_DEPTH = 0.1;
const FRAME_DISTANCE_FROM_WALL = 0.01;
const MAX_FRAMES_PER_WALL = 4;

// 图片列表
const images = [
    "jongsun-lee-F-pSZO_jeE8.jpg",
    "anders-jildén-5sxQH0ugTaA.jpg",
    "marcus-löfvenberg-Xz1ncdtqMR0.jpg",
    "tyler-lastovich-3shfnfzdFVc.jpg",
    "chuttersnap-9FyXCm6yu_g.jpg",
    "mungyu-kim-Ex57cKpwdnE.jpg",
    "anthony-intraversato-vYRAP3yMa3I.jpg",
    "anjali-mehta-TPej8i22DXw.jpg"
];

// 文档列表
const documents = [
    "A Neural Attention Model for Abstractive Sentence Summarization.pdf",
    "A Structured Self-Attentive Sentence Embedding.pdf",
    "Effective Approaches to Attention-based Neural Machine Translation.pdf",
    "Efficient Estimation of Word Representations in Vector Space.pdf",
    "A Neural Probabilistic Language Model.pdf"
];

// 创建画廊应用
async function createGallery() {
    try {
        log("开始创建画廊...");
        
        // 创建场景
        scene = new THREE.Scene();
        scene.background = new THREE.Color(0x000000);
        
        // 射线检测器和可点击对象
        raycaster = new THREE.Raycaster();
        mouse = new THREE.Vector2();
        
        // 创建相机
        camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 100);
        
        // 设置相机位置 - 站在走廊的起点，朝向走廊深处
        camera.position.set(0, 1.7, 2); // x, y, z: 中心线上，人眼高度，靠近入口处
        
        // 创建渲染器
        renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        document.getElementById('container').innerHTML = '';
        document.getElementById('container').appendChild(renderer.domElement);
        
        // 使用欧拉角旋转相机，使其朝向Z轴正方向
        const euler = new THREE.Euler(0, Math.PI, 0, 'YXZ');
        camera.rotation.copy(euler);
        
        // 现在创建控制器，它将保持相机当前朝向
        try {
            controls = new PointerLockControls(camera, document.body);
            if (!controls) {
                throw new Error('Failed to create PointerLockControls');
            }
        } catch (error) {
            log(`创建PointerLockControls时出错: ${error.message}`);
            // 即使控制器创建失败，也继续创建画廊
            controls = null;
        }
        
        // 点击事件处理
        document.getElementById('container').addEventListener('click', (event) => {
            // 如果正在查看资源，忽略点击
            if (isViewingResource) return;
            
            // 如果控制器已锁定，无需处理点击事件（已在3D环境中）
            if (controls && controls.isLocked) return;
            
            // 计算鼠标位置的归一化设备坐标
            mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
            mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
            
            // 设置射线
            raycaster.setFromCamera(mouse, camera);
            
            // 检测射线与可点击对象的交点
            const intersects = raycaster.intersectObjects(clickableObjects);
            
            if (intersects.length > 0) {
                const object = intersects[0].object;
                if (object.userData && object.userData.isClickable) {
                    log(`点击了资源: ${object.userData.resourceName}`);
                    
                    // 显示资源查看器
                    showResourceViewer(
                        object.userData.resourceName,
                        object.userData.resourceType,
                        object.userData.filePath
                    );
                    return; // 阻止锁定
                }
            }
            
            // 如果没有点击物体且控制器存在，尝试锁定
            if (controls) {
                try {
                    controls.lock();
                } catch (error) {
                    log(`锁定控制器时出错: ${error.message}`);
                }
            }
        });
        
        // 控制器事件监听
        if (controls) {
            controls.addEventListener('lock', () => {
                document.getElementById('info').style.display = 'none';
                document.getElementById('controls').style.display = 'none';
                document.getElementById('debug').style.display = 'none';
                
                // 在锁定时，如果有保存的相机方向，则恢复它
                if (lastCameraRotation && !isViewingResource) {
                    camera.rotation.copy(lastCameraRotation);
                } else {
                    // 在锁定时，确保相机朝向画廊方向
                    setTimeout(() => {
                        resetCameraDirection();
                    }, 50);
                }
            });
            
            controls.addEventListener('unlock', () => {
                // 保存当前相机方向，除非是在查看资源
                if (!isViewingResource) {
                    lastCameraRotation = camera.rotation.clone();
                }
                
                document.getElementById('info').style.display = 'block';
                document.getElementById('controls').style.display = 'block';
            });
        }
        
        // 键盘事件监听
        const onKeyDown = (event) => {
            switch (event.code) {
                case 'ArrowUp':
                case 'KeyW':
                    moveForward = true;
                    break;
                case 'ArrowLeft':
                case 'KeyA':
                    moveLeft = true;
                    break;
                case 'ArrowDown':
                case 'KeyS':
                    moveBackward = true;
                    break;
                case 'ArrowRight':
                case 'KeyD':
                    moveRight = true;
                    break;
            }
        };
        
        const onKeyUp = (event) => {
            switch (event.code) {
                case 'ArrowUp':
                case 'KeyW':
                    moveForward = false;
                    break;
                case 'ArrowLeft':
                case 'KeyA':
                    moveLeft = false;
                    break;
                case 'ArrowDown':
                case 'KeyS':
                    moveBackward = false;
                    break;
                case 'ArrowRight':
                case 'KeyD':
                    moveRight = false;
                    break;
            }
        };
        
        document.addEventListener('keydown', onKeyDown);
        document.addEventListener('keyup', onKeyUp);
        
        // 窗口大小变化监听
        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });
        
        // 材质
        materials = {
            wall: new THREE.MeshStandardMaterial({ color: 0x222222, roughness: 0.8 }),
            floor: new THREE.MeshStandardMaterial({ color: 0x333333, roughness: 0.8 }),
            frame: new THREE.MeshStandardMaterial({ color: 0x8B4513, roughness: 0.7 })
        };
        
        // 创建地板
        const floorGeometry = new THREE.PlaneGeometry(GALLERY_WIDTH, GALLERY_LENGTH);
        const floor = new THREE.Mesh(floorGeometry, materials.floor);
        floor.rotation.x = -Math.PI / 2;
        floor.position.y = 0;
        floor.position.z = GALLERY_LENGTH / 2;
        scene.add(floor);
        
        // 创建天花板
        const ceiling = new THREE.Mesh(floorGeometry, materials.floor);
        ceiling.rotation.x = Math.PI / 2;
        ceiling.position.y = GALLERY_HEIGHT;
        ceiling.position.z = GALLERY_LENGTH / 2;
        scene.add(ceiling);
        
        // 创建墙壁
        // 左墙
        const wallGeometry = new THREE.BoxGeometry(WALL_THICKNESS, GALLERY_HEIGHT, GALLERY_LENGTH);
        const leftWall = new THREE.Mesh(wallGeometry, materials.wall);
        leftWall.position.set(-GALLERY_WIDTH / 2 - WALL_THICKNESS / 2, GALLERY_HEIGHT / 2, GALLERY_LENGTH / 2);
        scene.add(leftWall);
        
        // 右墙
        const rightWall = new THREE.Mesh(wallGeometry, materials.wall);
        rightWall.position.set(GALLERY_WIDTH / 2 + WALL_THICKNESS / 2, GALLERY_HEIGHT / 2, GALLERY_LENGTH / 2);
        scene.add(rightWall);
        
        // 前墙
        const endWallGeometry = new THREE.BoxGeometry(GALLERY_WIDTH + WALL_THICKNESS * 2, GALLERY_HEIGHT, WALL_THICKNESS);
        const frontWall = new THREE.Mesh(endWallGeometry, materials.wall);
        frontWall.position.set(0, GALLERY_HEIGHT / 2, -WALL_THICKNESS / 2);
        scene.add(frontWall);
        
        // 后墙
        const backWall = new THREE.Mesh(endWallGeometry, materials.wall);
        backWall.position.set(0, GALLERY_HEIGHT / 2, GALLERY_LENGTH + WALL_THICKNESS / 2);
        scene.add(backWall);
        
        // 添加光源
        // 环境光
        const ambientLight = new THREE.AmbientLight(0x555555, 1.0);
        scene.add(ambientLight);
        
        // 走廊灯光
        for (let z = FRAME_SPACING; z < GALLERY_LENGTH; z += FRAME_SPACING * 2) {
            const light = new THREE.PointLight(0xffffcc, 0.8, 10);
            light.position.set(0, GALLERY_HEIGHT - 0.5, z);
            scene.add(light);
            
            const lightIndicator = new THREE.Mesh(
                new THREE.SphereGeometry(0.1, 8, 8),
                new THREE.MeshBasicMaterial({ color: 0xffffcc })
            );
            lightIndicator.position.copy(light.position);
            scene.add(lightIndicator);
        }
        
        return true;
    } catch (error) {
        log(`创建画廊时出错: ${error.message}`);
        return false;
    }
}

// 碰撞检测
function checkCollision(position) {
    const buffer = 0.5;
    
    // 左右墙碰撞
    if (position.x < -GALLERY_WIDTH / 2 + buffer) {
        position.x = -GALLERY_WIDTH / 2 + buffer;
    }
    if (position.x > GALLERY_WIDTH / 2 - buffer) {
        position.x = GALLERY_WIDTH / 2 - buffer;
    }
    
    // 前后墙碰撞
    if (position.z < buffer) {
        position.z = buffer;
    }
    if (position.z > GALLERY_LENGTH - buffer) {
        position.z = GALLERY_LENGTH - buffer;
    }
    
    return position;
}

// 初始化画廊
async function initGallery() {
    try {
        log("初始化画廊...");
        
        // 创建资源查看器UI
        createViewerUI();
        
        // 加载文件列表
        const { images, documents } = await loadFiles();
        
        if (images.length === 0 && documents.length === 0) {
            log("没有找到任何图片或PDF文件");
            document.getElementById('loading').textContent = '没有找到任何可显示的文件';
            return;
        }
        
        // 创建画廊
        const galleryCreated = await createGallery();
        if (!galleryCreated) {
            log("创建画廊失败");
            document.getElementById('loading').textContent = '创建画廊失败';
            return;
        }
        
        // 根据文件类型决定显示方式
        if (images.length > 0) {
            // 如果有图片，按原方式显示
            await addFramesToWall('left', images, true);
            await addFramesToWall('right', documents, false);
        } else {
            // 如果没有图片，只显示PDF文件
            log("没有找到图片文件，将PDF文件按编号交替显示在两侧");
            
            // 按编号分配文档到左右墙：奇数编号→左墙，偶数编号→右墙
            const leftWallDocs = [];
            const rightWallDocs = [];
            
            documents.forEach((docName, index) => {
                // 提取文件名开头的数字
                const match = docName.match(/^(\d+)/);
                if (match) {
                    const fileNumber = parseInt(match[1]);
                    if (fileNumber % 2 === 1) {
                        // 奇数编号放左墙
                        leftWallDocs.push(docName);
                        log(`文档 ${docName} (编号${fileNumber}) → 左墙第${leftWallDocs.length}位置`);
                    } else {
                        // 偶数编号放右墙
                        rightWallDocs.push(docName);
                        log(`文档 ${docName} (编号${fileNumber}) → 右墙第${rightWallDocs.length}位置`);
                    }
                } else {
                    // 如果没有数字编号，按原有逻辑分配
                    if (index % 2 === 0) {
                        leftWallDocs.push(docName);
                    } else {
                        rightWallDocs.push(docName);
                    }
                    log(`文档 ${docName} (无编号) → ${index % 2 === 0 ? '左' : '右'}墙`);
                }
            });
            
            // 对左墙和右墙的文档按编号排序
            leftWallDocs.sort((a, b) => {
                const matchA = a.match(/^(\d+)/);
                const matchB = b.match(/^(\d+)/);
                if (matchA && matchB) {
                    return parseInt(matchA[1]) - parseInt(matchB[1]);
                }
                return a.localeCompare(b);
            });
            
            rightWallDocs.sort((a, b) => {
                const matchA = a.match(/^(\d+)/);
                const matchB = b.match(/^(\d+)/);
                if (matchA && matchB) {
                    return parseInt(matchA[1]) - parseInt(matchB[1]);
                }
                return a.localeCompare(b);
            });
            
            log(`最终分配: 左墙${leftWallDocs.length}个文档, 右墙${rightWallDocs.length}个文档`);
            log(`左墙文档（按编号排序）: ${leftWallDocs.join(', ')}`);
            log(`右墙文档（按编号排序）: ${rightWallDocs.join(', ')}`);
            
            // 添加文档到对应墙壁
            if (leftWallDocs.length > 0) {
                await addFramesToWall('left', leftWallDocs, false);
            }
            if (rightWallDocs.length > 0) {
                await addFramesToWall('right', rightWallDocs, false);
            }
        }
        
        // 隐藏加载提示
        document.getElementById('loading').style.display = 'none';
        
        // 开始动画循环
        animate();
        
        // 显示欢迎指南
        showWelcomeGuide();
    } catch (error) {
        log(`初始化画廊时出错: ${error.message}`);
        document.getElementById('loading').textContent = `初始化画廊时出错: ${error.message}`;
        document.getElementById('loading').style.backgroundColor = 'rgba(255,0,0,0.7)';
    }
}

// 动画循环
const clock = new THREE.Clock();

// 重置相机方向，确保面向画廊
function resetCameraDirection() {
    // 使相机直接面向长廊中心（Z轴正方向）
    const euler = new THREE.Euler(0, Math.PI, 0, 'YXZ');
    camera.rotation.copy(euler);
    log("相机已重置，面向画廊长廊");
}

function animate() {
    requestAnimationFrame(animate);
    
    const delta = clock.getDelta();
    const moveSpeed = 5.0 * delta;
    
    // 处理移动
    velocity.x = 0;
    velocity.z = 0;
    
    direction.z = Number(moveForward) - Number(moveBackward);
    direction.x = Number(moveRight) - Number(moveLeft);
    direction.normalize();
    
    if (moveForward || moveBackward) velocity.z -= direction.z * moveSpeed;
    if (moveLeft || moveRight) velocity.x -= direction.x * moveSpeed;
    
    // 只有在 controls 存在且已锁定时才处理移动
    if (controls && controls.isLocked) {
        controls.moveRight(-velocity.x);
        controls.moveForward(-velocity.z);
        
        // 碰撞检测
        camera.position.copy(checkCollision(camera.position));
    }
    
    // 只有在 scene 和 camera 都存在时才渲染
    if (scene && camera && renderer) {
        renderer.render(scene, camera);
    }
}

animate();

// 开始加载画廊
initGallery();

// 创建资源查看器UI
function createViewerUI() {
    // 创建模糊叠加层
    blurOverlay = document.createElement('div');
    blurOverlay.style.position = 'fixed';
    blurOverlay.style.top = '0';
    blurOverlay.style.left = '0';
    blurOverlay.style.width = '100%';
    blurOverlay.style.height = '100%';
    blurOverlay.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
    blurOverlay.style.backdropFilter = 'blur(10px)';
    blurOverlay.style.zIndex = '1000';
    blurOverlay.style.display = 'none';
    blurOverlay.style.opacity = '0';
    blurOverlay.style.transition = 'opacity 0.5s ease';
    document.body.appendChild(blurOverlay);

    // 创建查看器容器
    viewerContainer = document.createElement('div');
    viewerContainer.style.position = 'fixed';
    viewerContainer.style.top = '50%';
    viewerContainer.style.left = '50%';
    viewerContainer.style.transform = 'translate(-50%, -50%) scale(0.8)';
    viewerContainer.style.maxWidth = '95%';
    viewerContainer.style.maxHeight = '90%';
    viewerContainer.style.overflow = 'hidden';
    viewerContainer.style.zIndex = '1001';
    viewerContainer.style.display = 'none';
    viewerContainer.style.transition = 'transform 0.5s ease';
    viewerContainer.style.boxShadow = '0 5px 25px rgba(0,0,0,0.3)';
    document.body.appendChild(viewerContainer);

    // 创建下载按钮
    downloadButton = document.createElement('button');
    downloadButton.textContent = '下载';
    downloadButton.style.position = 'fixed';
    downloadButton.style.bottom = '30px';
    downloadButton.style.left = '50%';
    downloadButton.style.transform = 'translateX(-50%)';
    downloadButton.style.padding = '10px 20px';
    downloadButton.style.backgroundColor = '#4CAF50';
    downloadButton.style.color = 'white';
    downloadButton.style.border = 'none';
    downloadButton.style.borderRadius = '5px';
    downloadButton.style.cursor = 'pointer';
    downloadButton.style.zIndex = '1002';
    downloadButton.style.display = 'none';
    downloadButton.style.opacity = '0';
    downloadButton.style.transition = 'opacity 0.5s ease';
    document.body.appendChild(downloadButton);

    // 创建关闭按钮
    closeButton = document.createElement('button');
    closeButton.textContent = '×';
    closeButton.style.position = 'fixed';
    closeButton.style.top = '20px';
    closeButton.style.right = '20px';
    closeButton.style.width = '40px';
    closeButton.style.height = '40px';
    closeButton.style.borderRadius = '50%';
    closeButton.style.backgroundColor = '#f44336';
    closeButton.style.color = 'white';
    closeButton.style.border = 'none';
    closeButton.style.fontSize = '24px';
    closeButton.style.cursor = 'pointer';
    closeButton.style.zIndex = '1002';
    closeButton.style.display = 'none';
    closeButton.style.opacity = '0';
    closeButton.style.transition = 'opacity 0.5s ease';
    document.body.appendChild(closeButton);

    // 添加下载按钮事件
    downloadButton.addEventListener('click', function() {
        if (currentFilePath) {
            // 创建一个下载链接
            const link = document.createElement('a');
            link.href = currentFilePath;
            link.download = currentResource;
            
            // 对于PDF和图片文件的特殊处理
            if (currentFileType === 'pdf') {
                // PDF文件，直接下载
                link.setAttribute('download', currentResource);
                link.setAttribute('target', '_blank');
                link.textContent = '下载PDF';
            } else if (currentFileType === 'image') {
                // 图片文件
                link.setAttribute('download', currentResource);
            }
            
            // 触发下载
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // 显示下载提示
            const downloadMsg = document.createElement('div');
            downloadMsg.textContent = `正在下载: ${currentResource}`;
            downloadMsg.style.position = 'fixed';
            downloadMsg.style.bottom = '80px';
            downloadMsg.style.left = '50%';
            downloadMsg.style.transform = 'translateX(-50%)';
            downloadMsg.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
            downloadMsg.style.color = 'white';
            downloadMsg.style.padding = '10px 20px';
            downloadMsg.style.borderRadius = '5px';
            downloadMsg.style.zIndex = '1003';
            document.body.appendChild(downloadMsg);
            
            // 3秒后移除提示
            setTimeout(() => {
                document.body.removeChild(downloadMsg);
            }, 3000);
        }
    });

    // 添加关闭按钮事件
    closeButton.addEventListener('click', closeResourceViewer);
}

// 显示资源查看器
function showResourceViewer(resourceName, resourceType, filePath) {
    if (isViewingResource) return;
    isViewingResource = true;
    currentResource = resourceName;
    currentFilePath = filePath;
    currentFileType = resourceType;
    
    // 重新验证资源类型（避免缓存问题）
    const fileExt = resourceName.toLowerCase().split('.').pop();
    let correctedResourceType = resourceType;
    if (fileExt === 'pdf') {
        correctedResourceType = 'pdf';
    } else if (['docx', 'doc', 'xlsx', 'xls', 'pptx', 'ppt'].includes(fileExt)) {
        correctedResourceType = 'document';
    }
    
    if (correctedResourceType !== resourceType) {
        resourceType = correctedResourceType;
    }
    
    // 解锁指针锁定前保存当前相机方向
    if (controls.isLocked) {
        lastCameraRotation = camera.rotation.clone();
        originalCameraPosition = camera.position.clone();
        controls.unlock();
    }
    
    // 清空查看器
    viewerContainer.innerHTML = '';
    
    // 根据资源类型显示内容
    if (resourceType === 'image') {
        // 创建图片容器
        const imgContainer = document.createElement('div');
        imgContainer.style.position = 'relative';
        imgContainer.style.maxWidth = '100%';
        imgContainer.style.maxHeight = '100%';
        imgContainer.style.display = 'flex';
        imgContainer.style.flexDirection = 'column';
        imgContainer.style.alignItems = 'center';
        viewerContainer.appendChild(imgContainer);
        
        // 添加标题
        const imgTitle = document.createElement('div');
        imgTitle.textContent = resourceName;
        imgTitle.style.color = 'white';
        imgTitle.style.fontSize = '18px';
        imgTitle.style.fontWeight = 'bold';
        imgTitle.style.marginBottom = '15px';
        imgTitle.style.textShadow = '0 1px 3px rgba(0,0,0,0.6)';
        imgContainer.appendChild(imgTitle);
        
        // 添加图片
        const img = document.createElement('img');
        img.src = filePath;
        img.style.maxWidth = '100%';
        img.style.maxHeight = 'calc(80vh - 100px)';
        img.style.objectFit = 'contain';
        img.style.display = 'block';
        img.style.margin = '0 auto';
        img.style.boxShadow = '0 5px 15px rgba(0,0,0,0.3)';
        img.style.borderRadius = '3px';
        imgContainer.appendChild(img);
        
        // 添加图片使用说明
        const imgTips = document.createElement('div');
        imgTips.style.color = 'white';
        imgTips.style.marginTop = '15px';
        imgTips.style.fontSize = '14px';
        imgTips.style.backgroundColor = 'rgba(0,0,0,0.5)';
        imgTips.style.padding = '8px 15px';
        imgTips.style.borderRadius = '5px';
        imgTips.style.maxWidth = '80%';
        imgTips.innerHTML = `
            <p style="margin: 0; text-align: center;">按ESC键或点击右上角×按钮返回画廊，点击下方按钮可下载图片</p>
        `;
        imgContainer.appendChild(imgTips);
    } else if (resourceType === 'pdf') {
        // 创建PDF预览容器
        const pdfContainer = document.createElement('div');
        pdfContainer.style.backgroundColor = 'white';
        pdfContainer.style.padding = '20px';
        pdfContainer.style.borderRadius = '10px';
        pdfContainer.style.width = '900px';
        pdfContainer.style.maxWidth = '90vw';
        pdfContainer.style.height = '80vh';
        pdfContainer.style.maxHeight = '85vh';
        pdfContainer.style.overflow = 'auto';
        pdfContainer.style.position = 'relative';
        viewerContainer.appendChild(pdfContainer);
        
        // 添加加载提示
        const loadingText = document.createElement('div');
        loadingText.textContent = 'PDF加载中...';
        loadingText.style.position = 'absolute';
        loadingText.style.top = '50%';
        loadingText.style.left = '50%';
        loadingText.style.transform = 'translate(-50%, -50%)';
        loadingText.style.color = '#666';
        loadingText.style.fontSize = '18px';
        pdfContainer.appendChild(loadingText);
        
        // 创建PDF查看器
        try {
            // 确保PDF.js库已加载
            if (window.pdfjsLib) {
                // 设置workerSrc
                const pdfjsLib = window.pdfjsLib;
                pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/build/pdf.worker.min.js';
                
                // 加载PDF文件
                const loadingTask = pdfjsLib.getDocument(filePath);
                loadingTask.promise.then(function(pdf) {
                    // 移除加载提示
                    pdfContainer.removeChild(loadingText);
                    
                    // 添加标题
                    const titleDiv = document.createElement('div');
                    titleDiv.style.textAlign = 'center';
                    titleDiv.style.marginBottom = '15px';
                    titleDiv.style.fontWeight = 'bold';
                    titleDiv.style.fontSize = '20px';
                    titleDiv.textContent = resourceName;
                    pdfContainer.appendChild(titleDiv);
                    
                    // 添加阅读指引
                    const readingTips = document.createElement('div');
                    readingTips.style.backgroundColor = '#f8f9fa';
                    readingTips.style.padding = '10px';
                    readingTips.style.borderRadius = '5px';
                    readingTips.style.marginBottom = '15px';
                    readingTips.style.fontSize = '14px';
                    readingTips.style.color = '#555';
                    readingTips.innerHTML = `
                        <p style="margin: 0 0 5px 0"><strong>使用说明：</strong></p>
                        <ul style="margin: 0 0 5px 20px; padding: 0;">
                            <li>使用鼠标滚轮浏览所有页面</li>
                            <li>点击"返回顶部"或"查看结尾"快速导航</li>
                            <li>按ESC键或点击右上角×按钮返回画廊</li>
                            <li>点击下方下载按钮可获取完整PDF文件</li>
                        </ul>
                    `;
                    pdfContainer.appendChild(readingTips);
                    
                    // 添加快速导航按钮
                    const navButtons = document.createElement('div');
                    navButtons.style.display = 'flex';
                    navButtons.style.justifyContent = 'center';
                    navButtons.style.gap = '10px';
                    navButtons.style.marginBottom = '15px';
                    
                    // 返回顶部按钮
                    const topButton = document.createElement('button');
                    topButton.textContent = '返回顶部';
                    topButton.style.padding = '5px 10px';
                    topButton.style.backgroundColor = '#007bff';
                    topButton.style.color = 'white';
                    topButton.style.border = 'none';
                    topButton.style.borderRadius = '3px';
                    topButton.style.cursor = 'pointer';
                    topButton.addEventListener('click', () => {
                        pdfContainer.scrollTop = 0;
                    });
                    navButtons.appendChild(topButton);
                    
                    // 返回底部按钮
                    const bottomButton = document.createElement('button');
                    bottomButton.textContent = '查看结尾';
                    bottomButton.style.padding = '5px 10px';
                    bottomButton.style.backgroundColor = '#007bff';
                    bottomButton.style.color = 'white';
                    bottomButton.style.border = 'none';
                    bottomButton.style.borderRadius = '3px';
                    bottomButton.style.cursor = 'pointer';
                    bottomButton.addEventListener('click', () => {
                        pdfContainer.scrollTop = pdfContainer.scrollHeight;
                    });
                    navButtons.appendChild(bottomButton);
                    
                    pdfContainer.appendChild(navButtons);
                    
                    // 创建页面容器
                    const pagesContainer = document.createElement('div');
                    pagesContainer.style.display = 'flex';
                    pagesContainer.style.flexDirection = 'column';
                    pagesContainer.style.alignItems = 'center';
                    pdfContainer.appendChild(pagesContainer);
                    
                    // 显示页数信息
                    const pageInfo = document.createElement('div');
                    pageInfo.style.textAlign = 'center';
                    pageInfo.style.marginBottom = '15px';
                    pageInfo.style.color = '#666';
                    pageInfo.textContent = `PDF文件：共 ${pdf.numPages} 页`;
                    pdfContainer.appendChild(pageInfo);
                    
                    // 页面加载进度信息
                    const progressInfo = document.createElement('div');
                    progressInfo.style.textAlign = 'center';
                    progressInfo.style.marginBottom = '10px';
                    progressInfo.style.color = '#4CAF50';
                    progressInfo.style.fontSize = '14px';
                    pdfContainer.appendChild(progressInfo);
                    
                    // 渲染所有页面
                    let loadedPages = 0;
                    
                    // 创建加载页面的函数
                    function loadPage(pageNum) {
                        renderPage(pdf, pageNum, pagesContainer).then(() => {
                            loadedPages++;
                            progressInfo.textContent = `正在加载：${loadedPages}/${pdf.numPages} 页`;
                            
                            // 加载完成后移除进度信息
                            if (loadedPages === pdf.numPages) {
                                setTimeout(() => {
                                    progressInfo.style.display = 'none';
                                }, 1500);
                            }
                        });
                    }
                    
                    // 顺序加载所有页面
                    for (let i = 1; i <= pdf.numPages; i++) {
                        loadPage(i);
                    }
                }).catch(function(error) {
                    loadingText.textContent = `无法加载PDF: ${error.message}`;
                    loadingText.style.color = 'red';
                });
            } else {
                // PDF.js库未加载
                loadingText.textContent = 'PDF查看器未加载，请下载PDF文件后查看';
                loadingText.style.color = 'red';
            }
        } catch (error) {
            // 出错时显示错误信息
            const errorDiv = document.createElement('div');
            errorDiv.style.color = 'red';
            errorDiv.style.padding = '20px';
            errorDiv.textContent = `加载PDF预览失败: ${error.message}`;
            pdfContainer.appendChild(errorDiv);
        }
    } else if (resourceType === 'document') {
        // 创建文档预览容器
        const docContainer = document.createElement('div');
        docContainer.style.backgroundColor = 'white';
        docContainer.style.padding = '30px';
        docContainer.style.borderRadius = '10px';
        docContainer.style.width = '800px';
        docContainer.style.maxWidth = '90vw';
        docContainer.style.height = '80vh';
        docContainer.style.maxHeight = '85vh';
        docContainer.style.overflow = 'auto';
        docContainer.style.position = 'relative';
        docContainer.style.textAlign = 'center';
        viewerContainer.appendChild(docContainer);
        
        // 获取文件扩展名
        const fileExt = resourceName.toLowerCase().split('.').pop();
        let docIcon = '';
        let docTypeDesc = '';
        let docColor = '#4285f4';
        
        switch (fileExt) {
            case 'docx':
            case 'doc':
                docIcon = '📄';
                docTypeDesc = 'Word 文档';
                docColor = '#2b579a';
                break;
            case 'xlsx':
            case 'xls':
                docIcon = '📊';
                docTypeDesc = 'Excel 电子表格';
                docColor = '#217346';
                break;
            case 'pptx':
            case 'ppt':
                docIcon = '📈';
                docTypeDesc = 'PowerPoint 演示文稿';
                docColor = '#d24726';
                break;
            default:
                docIcon = '📝';
                docTypeDesc = '文档';
        }
        
        // 添加文档图标和信息
        const docIcon_div = document.createElement('div');
        docIcon_div.style.fontSize = '80px';
        docIcon_div.style.marginBottom = '20px';
        docIcon_div.textContent = docIcon;
        docContainer.appendChild(docIcon_div);
        
        // 添加文档标题
        const docTitle = document.createElement('div');
        docTitle.textContent = resourceName;
        docTitle.style.fontSize = '24px';
        docTitle.style.fontWeight = 'bold';
        docTitle.style.marginBottom = '10px';
        docTitle.style.color = docColor;
        docContainer.appendChild(docTitle);
        
        // 添加文档类型描述
        const docDesc = document.createElement('div');
        docDesc.textContent = docTypeDesc;
        docDesc.style.fontSize = '16px';
        docDesc.style.color = '#666';
        docDesc.style.marginBottom = '30px';
        docContainer.appendChild(docDesc);
        
        // 添加文档内容预览
        const contentPreview = document.createElement('div');
        contentPreview.style.backgroundColor = '#f8f9fa';
        contentPreview.style.padding = '20px';
        contentPreview.style.borderRadius = '8px';
        contentPreview.style.marginBottom = '20px';
        contentPreview.style.textAlign = 'left';
        contentPreview.style.maxHeight = '400px';
        contentPreview.style.overflow = 'auto';
        contentPreview.innerHTML = `
            <h3 style="margin: 0 0 15px 0; color: ${docColor};">📄 文档内容预览</h3>
            <div id="content-loading" style="text-align: center; color: #666; padding: 20px;">
                正在加载文档内容...
            </div>
        `;
        docContainer.appendChild(contentPreview);
        
        // 异步加载文档内容
        loadDocumentContent(resourceName, contentPreview, docColor);
        
        // 添加功能说明
        const docFeatures = document.createElement('div');
        docFeatures.style.backgroundColor = '#e8f5e8';
        docFeatures.style.padding = '15px';
        docFeatures.style.borderRadius = '8px';
        docFeatures.style.marginBottom = '20px';
        docFeatures.style.textAlign = 'left';
        docFeatures.innerHTML = `
            <h3 style="margin: 0 0 10px 0; color: ${docColor};">✨ 智能处理功能</h3>
            <p style="margin: 0; line-height: 1.6; font-size: 14px;">
                📝 <strong>自动提取：</strong>已提取所有文本内容 | 
                🧠 <strong>智能问答：</strong>支持内容查询 | 
                💾 <strong>知识库：</strong>已向量化存储
            </p>
        `;
        docContainer.appendChild(docFeatures);
        
        // 添加使用指引
        const docTips = document.createElement('div');
        docTips.style.backgroundColor = '#e3f2fd';
        docTips.style.padding = '15px';
        docTips.style.borderRadius = '8px';
        docTips.style.textAlign = 'left';
        docTips.innerHTML = `
            <h3 style="margin: 0 0 10px 0; color: #1976d2;">💡 使用建议</h3>
            <p style="margin: 0; line-height: 1.6; font-size: 14px;">
                💬 <strong>智能问答：</strong>在聊天窗口询问文档内容 | 
                📥 <strong>文件下载：</strong>点击下载按钮获取原文件 | 
                ⌨️ <strong>返回画廊：</strong>按ESC键或点击×按钮
            </p>
        `;
        docContainer.appendChild(docTips);
        
        // 添加示例问题
        const exampleQuestions = document.createElement('div');
        exampleQuestions.style.backgroundColor = '#f3e5f5';
        exampleQuestions.style.padding = '20px';
        exampleQuestions.style.borderRadius = '8px';
        exampleQuestions.style.textAlign = 'left';
        
        let questions = [];
        switch (fileExt) {
            case 'docx':
            case 'doc':
                questions = [
                    `"${resourceName}的主要内容是什么？"`,
                    `"这个文档讲了哪些要点？"`,
                    `"文档中有哪些重要信息？"`
                ];
                break;
            case 'xlsx':
            case 'xls':
                questions = [
                    `"${resourceName}包含哪些数据？"`,
                    `"表格中有什么统计信息？"`,
                    `"这个电子表格的内容摘要？"`
                ];
                break;
            case 'pptx':
            case 'ppt':
                questions = [
                    `"${resourceName}讲了什么主题？"`,
                    `"演示文稿的核心观点是什么？"`,
                    `"PPT中有哪些重要内容？"`
                ];
                break;
        }
        
        exampleQuestions.innerHTML = `
            <h3 style="margin: 0 0 15px 0; color: #7b1fa2;">🤔 试试这些问题</h3>
            <p style="margin: 0 0 10px 0; color: #666;">复制下面的问题到聊天窗口：</p>
            ${questions.map(q => `<div style="background: white; padding: 8px 12px; margin: 5px 0; border-radius: 4px; border-left: 3px solid #7b1fa2; font-family: monospace; cursor: pointer;" onclick="navigator.clipboard.writeText(${q}); this.style.background='#e8f5e8'; setTimeout(() => this.style.background='white', 1000);">${q}</div>`).join('')}
        `;
        docContainer.appendChild(exampleQuestions);
    } else {
        console.log('未知资源类型，使用默认处理:', resourceType);
        // 创建默认容器
        const defaultContainer = document.createElement('div');
        defaultContainer.style.backgroundColor = 'white';
        defaultContainer.style.padding = '30px';
        defaultContainer.style.borderRadius = '10px';
        defaultContainer.style.width = '800px';
        defaultContainer.style.maxWidth = '90vw';
        defaultContainer.style.height = '80vh';
        defaultContainer.style.maxHeight = '85vh';
        defaultContainer.style.overflow = 'auto';
        defaultContainer.style.position = 'relative';
        defaultContainer.style.textAlign = 'center';
        viewerContainer.appendChild(defaultContainer);
        
        defaultContainer.innerHTML = `
            <h2>未知文件类型</h2>
            <p>文件名: ${resourceName}</p>
            <p>资源类型: ${resourceType}</p>
            <p>文件路径: ${filePath}</p>
            <p>请联系管理员或尝试下载文件查看内容。</p>
        `;
    }
    
    // 显示UI元素
    blurOverlay.style.display = 'block';
    viewerContainer.style.display = 'block';
    downloadButton.style.display = 'block';
    closeButton.style.display = 'block';
    
    // 动画效果
    setTimeout(() => {
        blurOverlay.style.opacity = '1';
        viewerContainer.style.transform = 'translate(-50%, -50%) scale(1)';
        downloadButton.style.opacity = '1';
        closeButton.style.opacity = '1';
    }, 10);
}

// 加载文档内容
async function loadDocumentContent(resourceName, contentContainer, docColor) {
    try {
        
        // 调用后端API获取文档内容
        const response = await fetch('/api/document-content', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                filename: resourceName
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success && data.content) {
            // 清空加载提示
            contentContainer.innerHTML = `
                <h3 style="margin: 0 0 15px 0; color: ${docColor};">📄 文档内容预览</h3>
            `;
            
            // 创建内容显示区域
            const contentDiv = document.createElement('div');
            contentDiv.style.backgroundColor = 'white';
            contentDiv.style.padding = '15px';
            contentDiv.style.borderRadius = '5px';
            contentDiv.style.border = '1px solid #ddd';
            contentDiv.style.fontFamily = 'Arial, sans-serif';
            contentDiv.style.fontSize = '14px';
            contentDiv.style.lineHeight = '1.6';
            contentDiv.style.whiteSpace = 'pre-wrap';
            contentDiv.style.wordBreak = 'break-word';
            contentDiv.style.maxHeight = '350px';
            contentDiv.style.overflow = 'auto';
            
            // 处理文本内容，限制长度
            let displayContent = data.content;
            const maxLength = 2000;
            if (displayContent.length > maxLength) {
                displayContent = displayContent.substring(0, maxLength) + '\n\n... (内容过长，已截断。完整内容请使用下方聊天功能查询)';
            }
            
            contentDiv.textContent = displayContent;
            contentContainer.appendChild(contentDiv);
            
            // 添加统计信息
            const statsDiv = document.createElement('div');
            statsDiv.style.marginTop = '10px';
            statsDiv.style.fontSize = '12px';
            statsDiv.style.color = '#666';
            statsDiv.innerHTML = `
                📊 内容统计: ${data.content.length} 字符 | 
                📅 处理时间: ${data.metadata?.processed_time || '未知'} | 
                🔧 处理器: ${data.metadata?.processor || '未知'}
            `;
            contentContainer.appendChild(statsDiv);
            
        } else {
            throw new Error(data.error || '无法获取文档内容');
        }
        
            } catch (error) {
        contentContainer.innerHTML = `
            <h3 style="margin: 0 0 15px 0; color: ${docColor};">📄 文档内容预览</h3>
            <div style="text-align: center; color: #e74c3c; padding: 20px; background: #fdf2f2; border-radius: 5px;">
                <p><strong>⚠️ 内容加载失败</strong></p>
                <p style="font-size: 14px; margin: 10px 0;">错误: ${error.message}</p>
                <p style="font-size: 12px; color: #666;">请尝试使用下方聊天功能查询文档内容</p>
            </div>
        `;
    }
}

// 渲染PDF页面
function renderPage(pdf, pageNumber, container) {
    return new Promise((resolve, reject) => {
        pdf.getPage(pageNumber).then(function(page) {
            const scale = 1.5;
            const viewport = page.getViewport({ scale: scale });
            
            // 创建页面容器
            const pageContainer = document.createElement('div');
            pageContainer.style.margin = '15px auto';
            pageContainer.style.border = '1px solid #ddd';
            pageContainer.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
            pageContainer.style.width = `${viewport.width}px`;
            pageContainer.style.position = 'relative';
            container.appendChild(pageContainer);
            
            // 创建Canvas
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            canvas.width = viewport.width;
            canvas.height = viewport.height;
            pageContainer.appendChild(canvas);
            
            // 页码标签
            const pageLabel = document.createElement('div');
            pageLabel.textContent = `第 ${pageNumber} 页`;
            pageLabel.style.textAlign = 'center';
            pageLabel.style.padding = '8px';
            pageLabel.style.backgroundColor = 'rgba(0,0,0,0.05)';
            pageLabel.style.borderTop = '1px solid #ddd';
            pageLabel.style.fontSize = '14px';
            pageLabel.style.color = '#444';
            pageContainer.appendChild(pageLabel);
            
            // 渲染PDF内容到Canvas
            const renderContext = {
                canvasContext: context,
                viewport: viewport
            };
            
            const renderTask = page.render(renderContext);
            renderTask.promise.then(() => {
                resolve();
            }).catch((error) => {
                console.error(`Error rendering page ${pageNumber}: ${error}`);
                reject(error);
            });
        }).catch((error) => {
            console.error(`Error getting page ${pageNumber}: ${error}`);
            reject(error);
        });
    });
}

// 关闭资源查看器
function closeResourceViewer() {
    if (!isViewingResource) return;
    
    // 动画效果
    blurOverlay.style.opacity = '0';
    viewerContainer.style.transform = 'translate(-50%, -50%) scale(0.8)';
    downloadButton.style.opacity = '0';
    closeButton.style.opacity = '0';
    
    // 延迟隐藏元素
    setTimeout(() => {
        blurOverlay.style.display = 'none';
        viewerContainer.style.display = 'none';
        downloadButton.style.display = 'none';
        closeButton.style.display = 'none';
        
        // 重置状态
        isViewingResource = false;
        currentResource = null;
        currentFilePath = null;
        currentFileType = null;
        
        // 恢复相机位置并锁定控制
        if (originalCameraPosition) {
            camera.position.copy(originalCameraPosition);
            // 如果之前有保存相机方向，恢复它
            if (lastCameraRotation) {
                camera.rotation.copy(lastCameraRotation);
            }
            originalCameraPosition = null;
            controls.lock();
        }
    }, 500);
}

// 显示欢迎和使用说明
function showWelcomeGuide() {
    // 创建欢迎弹窗
    const welcomeGuide = document.createElement('div');
    welcomeGuide.style.position = 'fixed';
    welcomeGuide.style.top = '50%';
    welcomeGuide.style.left = '50%';
    welcomeGuide.style.transform = 'translate(-50%, -50%)';
    welcomeGuide.style.backgroundColor = 'rgba(0, 0, 0, 0.85)';
    welcomeGuide.style.color = 'white';
    welcomeGuide.style.padding = '25px';
    welcomeGuide.style.borderRadius = '10px';
    welcomeGuide.style.zIndex = '1000';
    welcomeGuide.style.maxWidth = '500px';
    welcomeGuide.style.boxShadow = '0 5px 25px rgba(0,0,0,0.5)';
    welcomeGuide.style.textAlign = 'left';
    welcomeGuide.style.lineHeight = '1.6';
    
    // 弹窗内容
    welcomeGuide.innerHTML = `
        <h2 style="text-align: center; margin-bottom: 15px; color: #4CAF50;">欢迎来到3D画廊</h2>
        
        <h3 style="color: #fff; margin: 10px 0;">基本操作：</h3>
        <ul style="padding-left: 20px; margin-bottom: 15px;">
            <li><b>移动：</b> 使用 W/A/S/D 或方向键移动</li>
            <li><b>视角控制：</b> 点击鼠标激活视角控制，移动鼠标转动视角</li>
            <li><b>退出控制：</b> 按ESC键关闭视角控制</li>
            <li><b>交互：</b> 点击墙上的图片或PDF查看详情</li>
        </ul>
        
        <h3 style="color: #fff; margin: 10px 0;">查看资源：</h3>
        <ul style="padding-left: 20px; margin-bottom: 20px;">
            <li>点击<b>图片</b>可放大查看，点击下载按钮可保存</li>
            <li>点击<b>PDF文件</b>可查看所有页面内容，支持滚动浏览</li>
            <li>查看资源时可随时点击右上角×按钮或按ESC键返回</li>
        </ul>
        
        <div style="text-align: center; margin-top: 20px;">
            <button id="start-control" style="padding: 8px 20px; background-color: #4CAF50; border: none; color: white; border-radius: 4px; cursor: pointer; font-size: 16px;">点击开始控制</button>
        </div>
    `;
    
    document.body.appendChild(welcomeGuide);
    
    // 添加开始控制按钮事件
    document.getElementById('start-control').addEventListener('click', function() {
        // 尝试锁定控制器
        if (controls) {
            try {
                controls.lock();
                // 渐变消失
                welcomeGuide.style.transition = 'opacity 0.5s ease';
                welcomeGuide.style.opacity = '0';
                setTimeout(() => {
                    if (document.body.contains(welcomeGuide)) {
                        document.body.removeChild(welcomeGuide);
                    }
                }, 500);
            } catch (error) {
                log(`锁定控制器时出错: ${error.message}`);
            }
        }
    });
    
    // 60秒后自动关闭
    setTimeout(() => {
        if (document.body.contains(welcomeGuide) && welcomeGuide.style.opacity !== '0') {
            welcomeGuide.style.transition = 'opacity 0.5s ease';
            welcomeGuide.style.opacity = '0';
            setTimeout(() => {
                if (document.body.contains(welcomeGuide)) {
                    document.body.removeChild(welcomeGuide);
                }
            }, 500);
        }
    }, 60000);
}

// 动态加载文件列表
async function loadFiles() {
    try {
        log("开始加载文件列表...");
        const response = await fetch('/images/');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error(`Expected JSON response but got ${contentType}`);
        }
        
        const data = await response.json();
        log(`成功加载文件列表: ${JSON.stringify(data)}`);
        
        if (!data.images && !data.documents) {
            throw new Error('Invalid response format');
        }
        
        return {
            images: data.images || [],
            documents: data.documents || []
        };
    } catch (error) {
        log(`加载文件列表失败: ${error.message}`);
        document.getElementById('loading').textContent = `加载文件列表失败: ${error.message}`;
        document.getElementById('loading').style.backgroundColor = 'rgba(255,0,0,0.7)';
        return { images: [], documents: [] };
    }
}

// 添加画框和图片到墙壁
async function addFramesToWall(side, fileList, isImage = true) {
    const wallPosition = side === 'left' ? -GALLERY_WIDTH / 2 : GALLERY_WIDTH / 2;
    const wallFacing = side === 'left' ? 1 : -1;
    
    const numFrames = Math.min(MAX_FRAMES_PER_WALL, fileList.length);
    log(`为${side}墙添加${numFrames}个画框`);
    
    // 添加每个文件的Promise到数组中
    const promises = [];
    
    for (let i = 0; i < numFrames; i++) {
        const fileName = fileList[i];
        const zPosition = (i + 1) * FRAME_SPACING;
        
        // 创建画框
        const frameGeometry = new THREE.BoxGeometry(FRAME_WIDTH + 0.2, FRAME_HEIGHT + 0.2, FRAME_DEPTH);
        const frame = new THREE.Mesh(frameGeometry, materials.frame);
        frame.position.set(
            wallPosition + (FRAME_DISTANCE_FROM_WALL + FRAME_DEPTH / 2) * wallFacing,
            GALLERY_HEIGHT / 2,
            zPosition
        );
        frame.rotation.y = Math.PI / 2 * wallFacing;
        scene.add(frame);
        
        // 创建加载框架的Promise
        const loadFramePromise = (async () => {
            try {
                // 创建图片或文档
                let texture;
                let resourceType;
                
                if (isImage) {
                    texture = await createImageTexture(fileName);
                    resourceType = 'image';
                } else {
                    // 对于文档，使用新的通用文档纹理创建函数
                    texture = createDocumentTexture(fileName);
                    
                    // 根据文件扩展名确定资源类型
                    const fileExt = fileName.toLowerCase().split('.').pop();
                    if (fileExt === 'pdf') {
                        resourceType = 'pdf';
                    } else if (['docx', 'doc', 'xlsx', 'xls', 'pptx', 'ppt'].includes(fileExt)) {
                        resourceType = 'document';
                    } else {
                        resourceType = 'pdf'; // 默认作为PDF处理
                    }
                    
                    // 调试信息
                    console.log(`文件 ${fileName} 的资源类型设置为: ${resourceType} (扩展名: ${fileExt})`)
                }
                
                const pictureMaterial = new THREE.MeshBasicMaterial({
                    map: texture,
                    side: THREE.FrontSide
                });
                
                const pictureGeometry = new THREE.PlaneGeometry(FRAME_WIDTH, FRAME_HEIGHT);
                const picture = new THREE.Mesh(pictureGeometry, pictureMaterial);
                picture.position.set(
                    wallPosition + (FRAME_DISTANCE_FROM_WALL + FRAME_DEPTH + 0.01) * wallFacing,
                    GALLERY_HEIGHT / 2,
                    zPosition
                );
                picture.rotation.y = Math.PI / 2 * wallFacing;
                scene.add(picture);
                
                // 为资源添加用户数据，以便识别点击
                picture.userData = {
                    isClickable: true,
                    resourceName: fileName,
                    resourceType: resourceType,
                    filePath: `images/${fileName}` // 所有文件都在images目录
                };
                
                // 添加到可点击对象列表
                clickableObjects.push(picture);
                
                // 为画框添加聚光灯
                if (i === 0 || i === numFrames - 1 || i % 2 === 0) {
                    const spotLight = new THREE.SpotLight(0xffffff, 5, 8, Math.PI / 6);
                    spotLight.position.set(
                        wallPosition - 0.5 * wallFacing,
                        GALLERY_HEIGHT - 0.5,
                        zPosition
                    );
                    spotLight.target = picture;
                    scene.add(spotLight);
                }
                
                return { success: true, fileName };
            } catch (err) {
                log(`添加${fileName}时出错: ${err}`);
                return { success: false, fileName, error: err };
            }
        })();
        
        promises.push(loadFramePromise);
    }
    
    // 并行加载所有图片，但不会因一个失败而停止整个过程
    const results = await Promise.allSettled(promises);
    
    // 处理结果
    let successCount = 0;
    let failCount = 0;
    
    results.forEach(result => {
        if (result.status === 'fulfilled') {
            if (result.value.success) {
                successCount++;
            } else {
                failCount++;
                log(`添加${result.value.fileName}失败: ${result.value.error}`);
            }
        } else {
            failCount++;
            log(`Promise被拒绝: ${result.reason}`);
        }
    });
    
    log(`${side}墙加载完成: ${successCount}成功, ${failCount}失败`);
    return { success: successCount, failed: failCount };
}

// 使用成功的图片加载方法 - 预加载图片
function createImageTexture(imageName) {
    return new Promise((resolve, reject) => {
        // 显示详细的加载信息
        document.getElementById('loading').textContent = `正在加载: ${imageName}`;
        document.getElementById('loading').style.display = 'block';
        
        const img = new Image();
        img.crossOrigin = "Anonymous"; // 添加跨域支持
        
        // 添加超时处理，防止无限等待
        const timeoutId = setTimeout(() => {
            log(`加载图片超时: ${imageName}`);
            document.getElementById('loading').textContent = `图片加载超时: ${imageName}`;
            document.getElementById('loading').style.backgroundColor = 'rgba(255,150,0,0.7)';
            
            // 创建超时占位图
            const canvas = document.createElement('canvas');
            canvas.width = 256;
            canvas.height = 256;
            const ctx = canvas.getContext('2d');
            
            ctx.fillStyle = '#fff0dd';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            ctx.fillStyle = '#ff8800';
            ctx.font = 'bold 24px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('加载超时', canvas.width / 2, canvas.height / 2 - 20);
            ctx.fillText(imageName, canvas.width / 2, canvas.height / 2 + 20);
            
            const errorTexture = new THREE.CanvasTexture(canvas);
            resolve(errorTexture); // 使用超时占位图替代
        }, 10000); // 10秒超时
        
        img.onload = function() {
            clearTimeout(timeoutId); // 取消超时计时器
            log(`成功加载图片: ${imageName}`);
            
            try {
                // 直接使用纹理加载器加载图片（使用已加载的图片作为源）
                const texture = new THREE.TextureLoader().load(img.src);
                resolve(texture);
            } catch (err) {
                log(`处理图片时出错: ${imageName} - ${err.message}`);
                
                // 使用备用方法
                try {
                    const texture = new THREE.Texture();
                    texture.image = img;
                    texture.needsUpdate = true;
                    resolve(texture);
                } catch (err2) {
                    log(`备用方法也失败: ${err2.message}`);
                    const errorTexture = createErrorTexture(imageName, `失败: ${err2.message}`);
                    resolve(errorTexture);
                }
            }
        };
        
        img.onerror = function(err) {
            clearTimeout(timeoutId); // 取消超时计时器
            log(`加载图片失败: ${imageName} - 错误: ${err}`);
            document.getElementById('loading').textContent = `图片加载失败: ${imageName}`;
            document.getElementById('loading').style.backgroundColor = 'rgba(255,0,0,0.7)';
            
            const errorTexture = createErrorTexture(imageName, '加载失败');
            resolve(errorTexture); // 使用错误占位图替代
        };
        
        // 创建错误占位图的辅助函数
        function createErrorTexture(filename, message) {
            const canvas = document.createElement('canvas');
            canvas.width = 256;
            canvas.height = 256;
            const ctx = canvas.getContext('2d');
            
            ctx.fillStyle = '#ffdddd';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            ctx.fillStyle = '#ff0000';
            ctx.font = 'bold 24px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(message, canvas.width / 2, canvas.height / 2 - 20);
            ctx.fillText(filename, canvas.width / 2, canvas.height / 2 + 20);
            
            return new THREE.CanvasTexture(canvas);
        }
        
        // 尝试不同的路径格式
        const fullPath = `images/${imageName}`;
        log(`尝试加载图片URL: ${fullPath}`);
        
        img.src = fullPath;
    });
}

// 创建文档预览纹理（支持多种格式）
function createDocumentTexture(docName) {
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 256;
    const ctx = canvas.getContext('2d');
    
    // 获取文件扩展名
    const fileExt = docName.toLowerCase().split('.').pop();
    let docIcon = '';
    let docType = '';
    let bgColor = '#ffffff';
    let iconColor = '#4285f4';
    
    // 根据文件类型设置图标和颜色
    switch (fileExt) {
        case 'pdf':
            docIcon = 'PDF';
            docType = 'PDF';
            bgColor = '#ffffff';
            iconColor = '#ff0000';
            break;
        case 'docx':
        case 'doc':
            docIcon = 'DOC';
            docType = 'Word';
            bgColor = '#e8f4fd';
            iconColor = '#2b579a';
            break;
        case 'xlsx':
        case 'xls':
            docIcon = 'XLS';
            docType = 'Excel';
            bgColor = '#e8f5e8';
            iconColor = '#217346';
            break;
        case 'pptx':
        case 'ppt':
            docIcon = 'PPT';
            docType = 'PowerPoint';
            bgColor = '#fff2e8';
            iconColor = '#d24726';
            break;
        default:
            docIcon = 'DOC';
            docType = '文档';
            bgColor = '#f5f5f5';
            iconColor = '#666666';
    }
    
    // 背景
    ctx.fillStyle = bgColor;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // 添加边框
    ctx.strokeStyle = iconColor;
    ctx.lineWidth = 2;
    ctx.strokeRect(10, 10, canvas.width - 20, canvas.height - 20);
    
    // 文档图标
    ctx.fillStyle = iconColor;
    ctx.font = 'bold 32px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(docIcon, canvas.width / 2, canvas.height / 2 - 40);
    
    // 文档类型
    ctx.fillStyle = iconColor;
    ctx.font = 'bold 16px Arial';
    ctx.fillText(docType, canvas.width / 2, canvas.height / 2 - 10);
    
    // 文档标题
    ctx.fillStyle = '#000000';
    ctx.font = '14px Arial';
    const title = docName.replace(/\.[^/.]+$/, ''); // 移除扩展名
    
    // 自动换行
    const words = title.split(' ');
    let line = '';
    let y = canvas.height / 2 + 20;
    
    for (let n = 0; n < words.length; n++) {
        const testLine = line + words[n] + ' ';
        const metrics = ctx.measureText(testLine);
        const testWidth = metrics.width;
        
        if (testWidth > canvas.width - 40 && n > 0) {
            ctx.fillText(line, canvas.width / 2, y);
            line = words[n] + ' ';
            y += 18;
            if (y > canvas.height - 30) break; // 防止超出画布
        } else {
            line = testLine;
        }
    }
    if (y <= canvas.height - 30) {
        ctx.fillText(line, canvas.width / 2, y);
    }
    
    const texture = new THREE.CanvasTexture(canvas);
    return texture;
}

// 为了保持向后兼容，保留原有的PDF函数
function createPDFTexture(pdfName) {
    return createDocumentTexture(pdfName);
}

// 初始化应用
function init() {
    try {
        log("开始初始化...");
        
        // 创建画廊
        if (createGallery()) {
            log("画廊初始化成功，开始加载资源...");
        } else {
            document.getElementById('loading').textContent = "创建画廊失败";
            document.getElementById('loading').style.backgroundColor = "rgba(255,0,0,0.7)";
        }
    } catch (error) {
        log(`初始化错误: ${error.message}`);
        document.getElementById('loading').textContent = `初始化错误: ${error.message}`;
        document.getElementById('loading').style.backgroundColor = "rgba(255,0,0,0.7)";
    }
}

// 启动应用
init(); 