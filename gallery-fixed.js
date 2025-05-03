import * as THREE from 'three';
import { PointerLockControls } from 'three/addons/controls/PointerLockControls.js';

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
function createGallery() {
    log("开始创建画廊...");
    
    // 创建场景
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x000000);
    
    // 创建相机
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 100);
    
    // 设置相机位置 - 站在走廊的起点，朝向走廊深处
    camera.position.set(0, 1.7, 2); // x, y, z: 中心线上，人眼高度，靠近入口处
    
    // 创建渲染器
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    document.getElementById('container').innerHTML = '';
    document.getElementById('container').appendChild(renderer.domElement);
    
    // 使用欧拉角旋转相机，使其朝向Z轴正方向
    const euler = new THREE.Euler(0, Math.PI, 0, 'YXZ');
    camera.rotation.copy(euler);
    
    // 现在创建控制器，它将保持相机当前朝向
    const controls = new PointerLockControls(camera, document.body);
    
    // 点击锁定鼠标
    document.getElementById('container').addEventListener('click', () => {
        controls.lock();
    });
    
    // 控制器事件监听
    controls.addEventListener('lock', () => {
        document.getElementById('info').style.display = 'none';
        document.getElementById('controls').style.display = 'none';
        document.getElementById('debug').style.display = 'none';
        
        // 在锁定时，确保相机朝向画廊方向
        setTimeout(() => {
            resetCameraDirection();
        }, 50);
    });
    
    controls.addEventListener('unlock', () => {
        document.getElementById('info').style.display = 'block';
        document.getElementById('controls').style.display = 'block';
        // 不再显示debug窗口
    });
    
    // 移动控制变量
    const velocity = new THREE.Vector3();
    const direction = new THREE.Vector3();
    let moveForward = false;
    let moveBackward = false;
    let moveLeft = false;
    let moveRight = false;
    
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
    const materials = {
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
    
    // 创建PDF预览纹理
    function createPDFTexture(pdfName) {
        const canvas = document.createElement('canvas');
        canvas.width = 256;
        canvas.height = 256;
        const ctx = canvas.getContext('2d');
        
        // 背景
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // PDF图标
        ctx.fillStyle = '#ff0000';
        ctx.font = 'bold 40px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('PDF', canvas.width / 2, canvas.height / 2 - 50);
        
        // 文档标题
        ctx.fillStyle = '#000000';
        ctx.font = '20px Arial';
        const title = pdfName.replace('.pdf', '');
        
        // 自动换行
        const words = title.split(' ');
        let line = '';
        let y = canvas.height / 2;
        
        for (let n = 0; n < words.length; n++) {
            const testLine = line + words[n] + ' ';
            const metrics = ctx.measureText(testLine);
            const testWidth = metrics.width;
            
            if (testWidth > canvas.width - 40 && n > 0) {
                ctx.fillText(line, canvas.width / 2, y);
                line = words[n] + ' ';
                y += 25;
            } else {
                line = testLine;
            }
        }
        ctx.fillText(line, canvas.width / 2, y);
        
        const texture = new THREE.CanvasTexture(canvas);
        return texture;
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
                    if (isImage) {
                        texture = await createImageTexture(fileName);
                    } else {
                        texture = createPDFTexture(fileName);
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
            // 强制显示加载提示
            document.getElementById('loading').style.display = 'block';
            document.getElementById('loading').textContent = '正在初始化画廊...';
            
            // 并行添加图片和文档
            const leftWallPromise = addFramesToWall('left', images, true);
            const rightWallPromise = addFramesToWall('right', documents, false);
            
            // 等待所有墙面加载完成
            const [leftResult, rightResult] = await Promise.all([leftWallPromise, rightWallPromise]);
            
            // 隐藏加载提示
            document.getElementById('loading').style.display = 'none';
            
            const totalSuccess = leftResult.success + rightResult.success;
            const totalFailed = leftResult.failed + rightResult.failed;
            
            log(`画廊创建完成: ${totalSuccess}个文件成功加载, ${totalFailed}个文件加载失败`);
            
            // 确保相机朝向画廊方向
            resetCameraDirection();
            
            // 如果有失败的文件，显示警告但不阻止画廊显示
            if (totalFailed > 0) {
                const warningDiv = document.createElement('div');
                warningDiv.style.position = 'absolute';
                warningDiv.style.bottom = '10px';
                warningDiv.style.right = '10px';
                warningDiv.style.backgroundColor = 'rgba(255,165,0,0.7)';
                warningDiv.style.color = 'white';
                warningDiv.style.padding = '10px';
                warningDiv.style.borderRadius = '5px';
                warningDiv.style.zIndex = '100';
                warningDiv.textContent = `警告: ${totalFailed}个文件加载失败。画廊仍可浏览。`;
                document.body.appendChild(warningDiv);
                
                // 5秒后自动隐藏
                setTimeout(() => {
                    warningDiv.style.opacity = '0';
                    warningDiv.style.transition = 'opacity 1s';
                    
                    // 1秒后移除元素
                    setTimeout(() => {
                        if (document.body.contains(warningDiv)) {
                            document.body.removeChild(warningDiv);
                        }
                    }, 1000);
                }, 5000);
            }
        } catch (err) {
            log(`初始化画廊出错: ${err}`);
            document.getElementById('loading').textContent = `加载出错: ${err}`;
            document.getElementById('loading').style.backgroundColor = 'rgba(255,0,0,0.7)';
            
            // 即使有错误也隐藏加载屏幕，5秒后
            setTimeout(() => {
                document.getElementById('loading').style.opacity = '0';
                document.getElementById('loading').style.transition = 'opacity 1s';
                
                // 1秒后完全隐藏
                setTimeout(() => {
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('loading').style.opacity = '1';
                }, 1000);
            }, 5000);
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
        
        controls.moveRight(-velocity.x);
        controls.moveForward(-velocity.z);
        
        // 碰撞检测
        camera.position.copy(checkCollision(camera.position));
        
        renderer.render(scene, camera);
    }
    
    animate();
    
    // 开始加载画廊
    initGallery();
    
    return true;
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