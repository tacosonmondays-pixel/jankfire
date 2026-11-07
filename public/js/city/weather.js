// Weather in the city. For now: the Commute's PAPER STORMS (DESIGN §4.11): blizzards of shredded paperwork that close the
// view to ~30 m and hide you from Late Fees. A storm rolls in for ~55 s every 3 minutes (the same for everyone: it's
// keyed on the clock); its strength `storm` (0-1) is the Commute's share of where you are x the storm's ramp.
// Drawn as one InstancedMesh of tumbling paper sheets in a box round the camera, plus fog that whites out.
import * as THREE from 'three';

const N = 1400, BOX = 46, PERIOD = 180, ON = 55, RAMP = 8;
export class Weather {
  constructor(scene) {
    const g = new THREE.PlaneGeometry(0.28, 0.36);
    const cols = new Float32Array(N * 3), c = new THREE.Color();
    const m = new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide, fog: true });
    this.mesh = new THREE.InstancedMesh(g, m, N);
    for (let i = 0; i < N; i++) { const k = Math.random(); c.setHex(k < 0.08 ? 0xff5050 : k < 0.3 ? 0xfff2b8 : k < 0.4 ? 0xdde8ff : 0xf6f2ea); this.mesh.setColorAt(i, c); }
    void cols;
    this.mesh.frustumCulled = false; this.mesh.count = 0; this.mesh.renderOrder = 3;
    scene.add(this.mesh);
    this.p = new Float32Array(N * 3); this.r = new Float32Array(N * 3); this.spin = new Float32Array(N * 3);
    for (let i = 0; i < N * 3; i++) { this.p[i] = (Math.random() - 0.5) * BOX; this.r[i] = Math.random() * 6.28; this.spin[i] = (Math.random() - 0.5) * 9; }
    this.storm = 0; this.was = false; this.m4 = new THREE.Matrix4(); this.q = new THREE.Quaternion(); this.e = new THREE.Euler(); this.v = new THREE.Vector3(); this.one = new THREE.Vector3(1, 1, 1);
  }
  // commute = 0-1, how much of the camera's spot is the Commute (district weights). returns the storm strength
  update(cam, dt, commute, now = Date.now() / 1000) {
    const ph = now % PERIOD, ramp = ph < ON ? Math.min(1, ph / RAMP, (ON - ph) / RAMP) : 0;
    const s = Math.max(0, Math.min(1, ramp * commute));
    this.storm += (s - this.storm) * Math.min(1, dt * 2);
    this.started = !this.was && this.storm > 0.3; this.was = this.storm > 0.3;
    const n = Math.round(N * this.storm);
    this.mesh.count = n;
    if (!n) return this.storm;
    // wind: mostly from the north-west, gusting; sheets fall slowly and tumble
    const gust = 1 + 0.6 * Math.sin(now * 0.7) + 0.3 * Math.sin(now * 2.3), wx = 11 * gust, wz = 7 * gust;
    const cx = cam.position.x, cy = cam.position.y, cz = cam.position.z, H = BOX / 2;
    for (let i = 0; i < n; i++) {
      const j = i * 3, p = this.p;
      p[j] += (wx + Math.sin(now * 3 + i) * 2) * dt; p[j + 1] += (Math.sin(now * 2 + i * 0.7) * 1.5 - 0.6) * dt; p[j + 2] += (wz + Math.cos(now * 2.6 + i) * 2) * dt;
      for (let k = 0; k < 3; k++) { if (p[j + k] > H) p[j + k] -= BOX; else if (p[j + k] < -H) p[j + k] += BOX; } // wrap round the camera
      this.r[j] += this.spin[j] * dt; this.r[j + 1] += this.spin[j + 1] * dt; this.r[j + 2] += this.spin[j + 2] * dt;
      this.q.setFromEuler(this.e.set(this.r[j], this.r[j + 1], this.r[j + 2]));
      this.mesh.setMatrixAt(i, this.m4.compose(this.v.set(cx + p[j], Math.max(cy - 6, cy + p[j + 1] * 0.5), cz + p[j + 2]), this.q, this.one));
    }
    this.mesh.instanceMatrix.needsUpdate = true;
    return this.storm;
  }
  // fog during a storm: white paper haze closing in
  fog(env) {
    if (!env || this.storm <= 0.01) return;
    const s = this.storm;
    const paper = new THREE.Color(0xe6ddcc);
    env.fog.lerp(paper, s * 0.85); env.mid.lerp(paper, s * 0.8); env.bot.lerp(paper, s * 0.8); env.top.lerp(paper, s * 0.55); // the sky goes white too
    env.near = env.near + (4 - env.near) * s; env.far = env.far + (34 - env.far) * s;
  }
  dispose() { this.mesh.removeFromParent(); this.mesh.geometry.dispose(); this.mesh.material.dispose(); }
}
