<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue';
import * as THREE from 'three';
import gsap from 'gsap';
import { useRouter } from 'vue-router';

// 引入后期处理模块
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';

const router = useRouter();
const canvasRef = ref(null);

// Three.js 核心对象
let scene, camera, renderer, composer, particlesMesh;
let mouseX = 0;
let mouseY = 0;
let windowHalfX = window.innerWidth / 2;
let windowHalfY = window.innerHeight / 2;

// --------------------------------------------------------
// 🎨 Three.js 初始化：构建 3D 辉光宇宙
// --------------------------------------------------------
const initThree = () => {
  scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x000000, 0.001);

  camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 1, 3000);
  camera.position.z = 1000;

  renderer = new THREE.WebGLRenderer({
    canvas: canvasRef.value,
    antialias: false,
    alpha: true
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // 优化性能
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.toneMapping = THREE.ReinhardToneMapping;

  // --- 💡 核心：后期处理 (Bloom 效果) ---
  const renderScene = new RenderPass(scene, camera);
  const bloomPass = new UnrealBloomPass(
    new THREE.Vector2(window.innerWidth, window.innerHeight),
    2.5,  // 强度 Strength: 越高越闪耀
    0.5,  // 半径 Radius
    0.85  // 阈值 Threshold
  );

  composer = new EffectComposer(renderer);
  composer.addPass(renderScene);
  composer.addPass(bloomPass);

  // --- 创建粒子奇点 ---
  const geometry = new THREE.BufferGeometry();
  const particleCount = 2500;
  const positions = [];
  const colors = [];
  const colorObj = new THREE.Color();

  for (let i = 0; i < particleCount; i++) {
    // 球形分布算法，让粒子更像一个星团
    const r = 1000 * Math.sqrt(Math.random());
    const theta = Math.random() * 2 * Math.PI;
    const phi = Math.acos(2 * Math.random() - 1);

    const x = r * Math.sin(phi) * Math.cos(theta);
    const y = r * Math.sin(phi) * Math.sin(theta);
    const z = r * Math.cos(phi);
    positions.push(x, y, z);

    // 赛博朋克：青蓝色与紫红色交织
    const mixedColor = Math.random() > 0.5 ? 0x00ffff : 0xff00ff;
    colorObj.setHex(mixedColor);
    colors.push(colorObj.r, colorObj.g, colorObj.b);
  }

  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));

  const material = new THREE.PointsMaterial({
    size: 4,
    vertexColors: true,
    transparent: true,
    opacity: 1,
    blending: THREE.AdditiveBlending
  });

  particlesMesh = new THREE.Points(geometry, material);
  scene.add(particlesMesh);
};

// --------------------------------------------------------
// 🔄 渲染与视差交互
// --------------------------------------------------------
const animate = () => {
  requestAnimationFrame(animate);
  const time = Date.now() * 0.0003;

  // 粒子缓慢旋转
  particlesMesh.rotation.y = time * 0.5;
  particlesMesh.rotation.z = time * 0.2;

  // 相机平滑跟随鼠标 (视差效果)
  camera.position.x += (mouseX - camera.position.x) * 0.03;
  camera.position.y += (-mouseY - camera.position.y) * 0.03;
  camera.lookAt(scene.position);

  // 使用后期处理组合器进行渲染
  composer.render();
};

const onMouseMove = (event) => {
  mouseX = (event.clientX - windowHalfX) * 0.8;
  mouseY = (event.clientY - windowHalfY) * 0.8;
};

const onResize = () => {
  windowHalfX = window.innerWidth / 2;
  windowHalfY = window.innerHeight / 2;
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
  composer.setSize(window.innerWidth, window.innerHeight);
};

onMounted(() => {
  initThree();
  animate();
  window.addEventListener('mousemove', onMouseMove);
  window.addEventListener('resize', onResize);

  // GSAP 动画：让 UI 元素有节奏地进场
  gsap.to(".glitch", { opacity: 1, scale: 1, duration: 1.2, ease: "back.out(1.7)" });
  gsap.to(".subtitle", { opacity: 1, y: 0, duration: 1, delay: 0.5 });
  gsap.to(".action-btn", { opacity: 1, duration: 1, delay: 1 });
});

onBeforeUnmount(() => {
  window.removeEventListener('mousemove', onMouseMove);
  window.removeEventListener('resize', onResize);
  if (renderer) renderer.dispose();
});

const backToSafety = () => {
  router.push('/');
};
</script>

<template>
  <div class="error-page">
    <canvas ref="canvasRef" class="canvas-3d"></canvas>

    <div class="ui-overlay">
      <div class="glitch-box">
        <h1 class="glitch" data-text="404">404</h1>
      </div>
      <p class="subtitle">DIMENSION_COLLAPSE: DATA_LOST</p>
      <p class="desc">你闯入了未知的数字荒原，这里只有数据的残骸。</p>

      <button class="action-btn" @click="backToSafety">
        返回主页
      </button>
    </div>
  </div>
</template>

<style scoped>
.error-page {
  position: relative;
  width: 100vw;
  height: 100vh;
  background-color: #000;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
}

.canvas-3d {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 1;
}

.ui-overlay {
  position: relative;
  z-index: 10;
  text-align: center;
  color: white;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  pointer-events: none;
}

/* 404 故障文字 */
.glitch {
  font-size: clamp(8rem, 20vw, 15rem);
  font-weight: 900;
  position: relative;
  opacity: 0;
  scale: 0.5;
  margin: 0;
  text-shadow: 0 0 30px rgba(255, 255, 255, 0.5);
}

.glitch::before, .glitch::after {
  content: attr(data-text);
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: black;
  clip: rect(0, 0, 0, 0);
}

.glitch::before {
  left: 3px;
  text-shadow: -2px 0 #ff00ff;
  animation: glitch-anim 3s infinite linear alternate-reverse;
}

.glitch::after {
  left: -3px;
  text-shadow: -2px 0 #00ffff;
  animation: glitch-anim2 2.5s infinite linear alternate-reverse;
}

.subtitle {
  font-size: 1.2rem;
  letter-spacing: 0.8rem;
  color: #00ffff;
  opacity: 0;
  transform: translateY(20px);
  margin-top: -20px;
  text-shadow: 0 0 10px #00ffff;
}

.action-btn {
  pointer-events: auto;
  margin-top: 50px;
  padding: 12px 35px;
  background: transparent;
  border: 1px solid #ff00ff;
  color: #ff00ff;
  font-weight: bold;
  letter-spacing: 2px;
  cursor: pointer;
  transition: all 0.3s;
  opacity: 0;
  box-shadow: 0 0 10px rgba(255, 0, 255, 0.2);
}

.action-btn:hover {
  background: #ff00ff;
  color: #000;
  box-shadow: 0 0 30px #ff00ff;
  transform: scale(1.05);
}

@keyframes glitch-anim {
  0% { clip: rect(10px, 9999px, 40px, 0); }
  20% { clip: rect(60px, 9999px, 80px, 0); }
  100% { clip: rect(20px, 9999px, 50px, 0); }
}

@keyframes glitch-anim2 {
  0% { clip: rect(70px, 9999px, 100px, 0); }
  50% { clip: rect(10px, 9999px, 30px, 0); }
  100% { clip: rect(40px, 9999px, 90px, 0); }
}
</style>