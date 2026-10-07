const canvas = document.getElementById('scene');
const ctx = canvas.getContext('2d');
const W = canvas.width;
const H = canvas.height;

const PADDING = 60;

let state = {
    cart: { x: 5, y: 4, angle: 0, left_speed: 0, right_speed: 0, target: null },
    anchors: [],
    distances: {},
    estimate: null,
    mesh: { min_x: 0, min_y: 0, max_x: 10, max_y: 8, noise_std: 0.05 },
};
let transform = null;

// ---------------------------------------------------------------- transform
function computeTransform() {
    const m = state.mesh;
    const mw = m.max_x - m.min_x;
    const mh = m.max_y - m.min_y;
    const s = Math.min((W - 2 * PADDING) / mw, (H - 2 * PADDING) / mh);
    return {
        scale: s,
        offsetX: PADDING + ((W - 2 * PADDING) - mw * s) / 2,
        offsetY: PADDING + ((H - 2 * PADDING) - mh * s) / 2,
        mx0: m.min_x, my1: m.max_y, mw, mh,
    };
}
function m2c(mx, my) {
    const t = transform;
    return [t.offsetX + (mx - t.mx0) * t.scale,
            t.offsetY + (t.my1 - my) * t.scale];
}
function c2m(cx, cy) {
    const t = transform;
    return [t.mx0 + (cx - t.offsetX) / t.scale,
            t.my1 - (cy - t.offsetY) / t.scale];
}
function mLen(v) { return v * transform.scale; }   // метры → пиксели

// ---------------------------------------------------------------- WebSocket
let ws;
function connect() {
    ws = new WebSocket(`ws://${location.host}/ws`);
    ws.onopen  = () => setWs('подключено', '#4ade80');
    ws.onclose = () => { setWs('переподключение…', '#f87171'); setTimeout(connect, 1000); };
    ws.onerror = () => setWs('ошибка', '#f87171');
    ws.onmessage = (ev) => { state = JSON.parse(ev.data); updateSidebar(); };
}
function send(obj) {
    if (ws?.readyState === WebSocket.OPEN) ws.send(JSON.stringify(obj));
}

// ---------------------------------------------------------------- draw
function drawGrid() {
    const m = state.mesh;
    const t = transform;

    // Поле
    const [x0, y0] = m2c(m.min_x, m.max_y);
    const [x1, y1] = m2c(m.max_x, m.min_y);
    ctx.fillStyle = '#f8fafc';
    ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
    ctx.strokeStyle = '#cbd5e1';
    ctx.lineWidth = 2;
    ctx.strokeRect(x0, y0, x1 - x0, y1 - y0);

    // Сетка 1 м
    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 1;
    for (let mx = Math.ceil(m.min_x); mx <= m.max_x; mx++) {
        const [cx] = m2c(mx, 0);
        ctx.beginPath(); ctx.moveTo(cx, y0); ctx.lineTo(cx, y1); ctx.stroke();
        ctx.fillStyle = '#94a3b8';
        ctx.font = '10px system-ui';
        ctx.fillText(`${mx}`, cx + 2, y1 - 4);
    }
    for (let my = Math.ceil(m.min_y); my <= m.max_y; my++) {
        const [, cy] = m2c(0, my);
        ctx.beginPath(); ctx.moveTo(x0, cy); ctx.lineTo(x1, cy); ctx.stroke();
        ctx.fillStyle = '#94a3b8';
        ctx.font = '10px system-ui';
        ctx.fillText(`${my} м`, x0 + 4, cy - 2);
    }

    // Оси системы координат мэша
    const [ox, oy] = m2c(m.min_x, m.min_y);
    ctx.strokeStyle = '#ef4444';   // X
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(ox, oy); ctx.lineTo(ox + 40, oy); ctx.stroke();
    ctx.fillStyle = '#ef4444'; ctx.font = 'bold 12px system-ui';
    ctx.fillText('X', ox + 44, oy + 4);

    ctx.strokeStyle = '#22c55e';   // Y
    ctx.beginPath(); ctx.moveTo(ox, oy); ctx.lineTo(ox, oy - 40); ctx.stroke();
    ctx.fillStyle = '#22c55e';
    ctx.fillText('Y', ox - 4, oy - 44);
}

function drawDistanceCircles() {
    const r = state.mesh.noise_std;
    ctx.save();
    ctx.setLineDash([6, 6]);
    ctx.lineWidth = 1.5;
    for (const a of state.anchors) {
        const d = state.distances[a.id];
        if (d == null) continue;
        const [cx, cy] = m2c(a.x, a.y);
        ctx.strokeStyle = 'rgba(56, 189, 248, .55)';
        ctx.beginPath();
        ctx.arc(cx, cy, mLen(d), 0, Math.PI * 2);
        ctx.stroke();
    }
    ctx.restore();
}

function drawDistanceLines() {
    const cart = state.cart;
    const [cx, cy] = m2c(cart.x, cart.y);
    ctx.font = 'bold 12px system-ui';
    ctx.textAlign = 'center';
    for (const a of state.anchors) {
        const d = state.distances[a.id];
        if (d == null) continue;
        const [ax, ay] = m2c(a.x, a.y);

        ctx.strokeStyle = 'rgba(56, 189, 248, .8)';
        ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.moveTo(ax, ay); ctx.lineTo(cx, cy); ctx.stroke();

        // Подпись расстояния — по середине линии
        const mx = (ax + cx) / 2, my = (ay + cy) / 2;
        const label = d.toFixed(2) + ' м';
        const w = ctx.measureText(label).width + 8;
        ctx.fillStyle = 'rgba(15, 23, 42, .85)';
        ctx.fillRect(mx - w / 2, my - 9, w, 16);
        ctx.fillStyle = '#38bdf8';
        ctx.fillText(label, mx, my + 3);
    }
    ctx.textAlign = 'start';
}

function drawAnchors() {
    for (const a of state.anchors) {
        const [cx, cy] = m2c(a.x, a.y);

        // Пульсирующий радиус действия
        ctx.beginPath();
        ctx.arc(cx, cy, 18, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(167, 139, 250, .18)';
        ctx.fill();

        // Иконка «вышка»: круг + крест
        ctx.beginPath();
        ctx.arc(cx, cy, 10, 0, Math.PI * 2);
        ctx.fillStyle = '#a78bfa';
        ctx.fill();
        ctx.strokeStyle = '#f8fafc';
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.strokeStyle = '#f8fafc';
        ctx.beginPath();
        ctx.moveTo(cx - 5, cy); ctx.lineTo(cx + 5, cy);
        ctx.moveTo(cx, cy - 5); ctx.lineTo(cx, cy + 5);
        ctx.stroke();

        // Метка якоря
        ctx.fillStyle = '#a78bfa';
        ctx.font = 'bold 13px system-ui';
        ctx.fillText(a.id, cx + 14, cy - 10);
    }
}

function drawCart(cx, cy, angle) {
    ctx.save();
    ctx.translate(cx, cy);
    // В canvas Y вниз, поэтому знак угла инвертируется
    ctx.rotate(-angle);

    const scale = transform.scale;
    const L = 0.7 * scale;   // длина корпуса, м
    const Wd = 0.5 * scale;  // ширина

    // Тень
    ctx.save();
    ctx.globalAlpha = 0.15;
    ctx.fillStyle = '#000';
    ctx.beginPath();
    ctx.ellipse(0, 6, L / 2, Wd / 2, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    // Колёса
    ctx.fillStyle = '#111827';
    const wW = L * 0.18, wH = Wd * 0.14;
    ctx.fillRect(-L / 2 + 4, -Wd / 2 - wH / 2 + 2, wW, wH);
    ctx.fillRect(-L / 2 + 4,  Wd / 2 - wH / 2 - 2, wW, wH);
    ctx.fillRect( L / 2 - wW - 4, -Wd / 2 - wH / 2 + 2, wW, wH);
    ctx.fillRect( L / 2 - wW - 4,  Wd / 2 - wH / 2 - 2, wW, wH);

    // Корпус
    ctx.fillStyle = '#3b82f6';
    ctx.beginPath();
    ctx.roundRect(-L / 2, -Wd / 2, L, Wd, 8);
    ctx.fill();

    // Кабина
    ctx.fillStyle = '#1d4ed8';
    ctx.beginPath();
    ctx.roundRect(-L * 0.15, -Wd * 0.3, L * 0.4, Wd * 0.6, 6);
    ctx.fill();

    // Указатель «носа»
    ctx.fillStyle = '#ef4444';
    ctx.beginPath();
    ctx.moveTo(L / 2 + 8, 0);
    ctx.lineTo(L / 2 - 2, -Wd * 0.25);
    ctx.lineTo(L / 2 - 2,  Wd * 0.25);
    ctx.closePath();
    ctx.fill();

    ctx.restore();
}

function drawEstimate() {
    if (!state.estimate) return;
    const [cx, cy] = m2c(state.estimate[0], state.estimate[1]);

    ctx.beginPath();
    ctx.arc(cx, cy, 12, 0, Math.PI * 2);
    ctx.strokeStyle = '#f59e0b';
    ctx.lineWidth = 2;
    ctx.setLineDash([4, 4]);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.beginPath();
    ctx.arc(cx, cy, 3, 0, Math.PI * 2);
    ctx.fillStyle = '#f59e0b';
    ctx.fill();
}

function drawTarget() {
    const t = state.cart.target;
    if (!t) return;
    const [cx, cy] = m2c(t[0], t[1]);

    // Пульс
    const phase = (performance.now() / 500) % 1;
    const r = 12 + phase * 20;
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(239, 68, 68, ${1 - phase})`;
    ctx.lineWidth = 2;
    ctx.stroke();

    // Крестовина
    ctx.strokeStyle = '#ef4444';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(cx - 10, cy); ctx.lineTo(cx + 10, cy);
    ctx.moveTo(cx, cy - 10); ctx.lineTo(cx, cy + 10);
    ctx.stroke();
}

// ---------------------------------------------------------------- render
function render() {
    if (!transform) transform = computeTransform();

    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, W, H);

    drawGrid();
    drawDistanceCircles();
    drawDistanceLines();
    drawAnchors();
    drawEstimate();
    drawTarget();

    // Тележка
    const [cx, cy] = m2c(state.cart.x, state.cart.y);
    drawCart(cx, cy, state.cart.angle);

    // Подпись «истинное положение»
    ctx.fillStyle = '#334155';
    ctx.font = 'bold 11px system-ui';
    ctx.fillText(`истина (${state.cart.x.toFixed(2)}, ${state.cart.y.toFixed(2)}) м`,
                 cx + 14, cy + 28);

    requestAnimationFrame(render);
}

// ---------------------------------------------------------------- sidebar
function setWs(text, color) {
    const el = document.getElementById('t-ws');
    el.textContent = text;
    el.style.color = color;
}
function speedLabel(v) {
    return v > 0 ? '▲' : v < 0 ? '▼' : '·';
}
function updateSidebar() {
    const c = state.cart;
    document.getElementById('t-true').textContent =
        `(${c.x.toFixed(2)}, ${c.y.toFixed(2)})`;
    document.getElementById('t-est').textContent = state.estimate
        ? `(${state.estimate[0].toFixed(2)}, ${state.estimate[1].toFixed(2)})`
        : '—';
    document.getElementById('t-err').textContent = state.estimate
        ? Math.hypot(state.estimate[0] - c.x, state.estimate[1] - c.y).toFixed(3) + ' м'
        : '—';
    document.getElementById('t-angle').textContent =
        ((c.angle * 180 / Math.PI) + 360) % 360 | 0;
    document.getElementById('t-left').textContent = speedLabel(c.left_speed);
    document.getElementById('t-right').textContent = speedLabel(c.right_speed);

    // Дистанции
    const ul = document.getElementById('distances');
    ul.innerHTML = '';
    for (const a of state.anchors) {
        const d = state.distances[a.id];
        const li = document.createElement('li');
        li.innerHTML = `<span class="id">${a.id}</span>` +
                       `<span class="val">${d != null ? d.toFixed(2) + ' м' : '—'}</span>`;
        ul.appendChild(li);
    }
}

// ---------------------------------------------------------------- input
document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT') return;
    const map = { KeyW: 'forward', KeyS: 'backward', KeyA: 'left', KeyD: 'right', Space: 'stop' };
    if (map[e.code]) { e.preventDefault(); send({ type: 'command', value: map[e.code] }); }
});
document.addEventListener('keyup', () => send({ type: 'command', value: 'stop' }));

document.querySelectorAll('.btn').forEach((b) => {
    const cmd = b.dataset.cmd;
    const fire = (e) => { e.preventDefault(); send({ type: 'command', value: cmd }); };
    const stop = (e) => { e.preventDefault(); send({ type: 'command', value: 'stop' }); };
    b.addEventListener('mousedown', fire);
    b.addEventListener('mouseup', stop);
    b.addEventListener('mouseleave', stop);
    b.addEventListener('touchstart', fire);
    b.addEventListener('touchend', stop);
});

// Клик по canvas — задать цель
canvas.addEventListener('click', (e) => {
    const rect = canvas.getBoundingClientRect();
    const cx = (e.clientX - rect.left) * (canvas.width / rect.width);
    const cy = (e.clientY - rect.top) * (canvas.height / rect.height);
    const [mx, my] = c2m(cx, cy);
    send({ type: 'target', x: +mx.toFixed(3), y: +my.toFixed(3) });
    document.getElementById('tx').value = mx.toFixed(2);
    document.getElementById('ty').value = my.toFixed(2);
});

document.getElementById('goto').addEventListener('click', () => {
    const x = parseFloat(document.getElementById('tx').value);
    const y = parseFloat(document.getElementById('ty').value);
    if (Number.isFinite(x) && Number.isFinite(y)) send({ type: 'target', x, y });
});
document.getElementById('cancel').addEventListener('click', () => send({ type: 'clear_target' }));

const noiseInput = document.getElementById('noise');
const noiseVal = document.getElementById('noise-val');
noiseInput.addEventListener('input', () => {
    const v = parseFloat(noiseInput.value);
    noiseVal.textContent = v.toFixed(2) + ' м';
    send({ type: 'noise', value: v });
});
noiseVal.textContent = (state.mesh?.noise_std ?? 0.05).toFixed(2) + ' м';

// ---------------------------------------------------------------- start
connect();
render();