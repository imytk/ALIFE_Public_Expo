/* =========================================================
   ALIFE PUBLIC EXPO — Hero Background Simulations
   Canvas fills the hero; a light tint is painted each frame
   so text stays readable while the simulation is fully visible.
   data-hero-bg on <header.hero> selects the simulation.
   ========================================================= */

(function () {
  'use strict';

  /* Shared palette */
  const CORAL      = [240, 120, 104];
  const PERI       = [155, 142, 196];
  const PERI_LT    = [196, 184, 232];
  const TEAL       = [100, 200, 175];

  /* Paint a semi-transparent gradient tint each frame so text stays readable */
  function tint(ctx, W, H) {
    const g = ctx.createLinearGradient(W, 0, 0, H);
    g.addColorStop(0,   'rgba(122,128,200,0.45)');
    g.addColorStop(0.5, 'rgba(184,120,160,0.38)');
    g.addColorStop(1,   'rgba(240,110,90,0.45)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);
  }

  const SIM = {

    /* ── INDEX: Boids flocking ── */
    boids: function (canvas, ctx, W, H) {
      const N = 140;
      const boids = Array.from({ length: N }, () => ({
        x: Math.random() * W, y: Math.random() * H,
        vx: (Math.random() - 0.5) * 2.2, vy: (Math.random() - 0.5) * 2.2,
        t: Math.random(),
      }));
      const SEP=28, ALI=60, COH=80, MS=2.4, MF=0.065;
      function lim(vx,vy,m){const s=Math.hypot(vx,vy);return s>m?[vx/s*m,vy/s*m]:[vx,vy];}

      return function tick() {
        for(let i=0;i<N;i++){
          const b=boids[i];
          let sx=0,sy=0,sn=0,ax=0,ay=0,an=0,cx=0,cy=0,cn=0;
          for(let j=0;j<N;j++){
            if(i===j)continue;
            const o=boids[j],dx=o.x-b.x,dy=o.y-b.y,d=Math.hypot(dx,dy);
            if(d<SEP&&d>0){sx-=dx/d;sy-=dy/d;sn++;}
            if(d<ALI){ax+=o.vx;ay+=o.vy;an++;}
            if(d<COH){cx+=o.x;cy+=o.y;cn++;}
          }
          let fx=0,fy=0;
          if(sn){const[lx,ly]=lim(sx/sn,sy/sn,MF);fx+=lx;fy+=ly;}
          if(an){const[lx,ly]=lim(ax/an-b.vx,ay/an-b.vy,MF);fx+=lx;fy+=ly;}
          if(cn){const[lx,ly]=lim(cx/cn-b.x,cy/cn-b.y,MF*0.5);fx+=lx;fy+=ly;}
          b.vx+=fx;b.vy+=fy;[b.vx,b.vy]=lim(b.vx,b.vy,MS);
          b.x=(b.x+b.vx+W)%W;b.y=(b.y+b.vy+H)%H;
        }
        ctx.fillStyle='rgba(24,22,53,0.25)';ctx.fillRect(0,0,W,H);
        for(const b of boids){
          const ang=Math.atan2(b.vy,b.vx);
          const r=Math.round(CORAL[0]*(1-b.t)+PERI[0]*b.t);
          const g=Math.round(CORAL[1]*(1-b.t)+PERI[1]*b.t);
          const bl=Math.round(CORAL[2]*(1-b.t)+PERI[2]*b.t);
          ctx.save();ctx.translate(b.x,b.y);ctx.rotate(ang);
          ctx.beginPath();ctx.moveTo(8,0);ctx.lineTo(-5,4);ctx.lineTo(-5,-4);ctx.closePath();
          ctx.fillStyle=`rgba(${r},${g},${bl},0.9)`;ctx.fill();
          ctx.restore();
        }
        tint(ctx,W,H);
      };
    },

    /* ── ZONE 1: Conway's Game of Life ── */
    gol: function (canvas, ctx, W, H) {
      const CELL=9;
      const COLS=Math.floor(W/CELL), ROWS=Math.floor(H/CELL);
      let grid=Array.from({length:ROWS},()=>Array.from({length:COLS},()=>Math.random()<0.32?1:0));
      let frame=0;
      function step(){
        grid=Array.from({length:ROWS},(_,r)=>Array.from({length:COLS},(_,c)=>{
          let n=0;
          for(let dr=-1;dr<=1;dr++)for(let dc=-1;dc<=1;dc++){
            if(dr===0&&dc===0)continue;
            n+=grid[(r+dr+ROWS)%ROWS][(c+dc+COLS)%COLS];
          }
          return grid[r][c]?(n===2||n===3?1:0):(n===3?1:0);
        }));
      }
      return function tick(){
        frame++;
        if(frame%5===0)step();
        ctx.fillStyle='rgba(24,22,53,0.3)';ctx.fillRect(0,0,W,H);
        for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++){
          if(grid[r][c]){
            const t=(r/ROWS+c/COLS)/2;
            const red=Math.round(PERI_LT[0]*(1-t)+CORAL[0]*t);
            const grn=Math.round(PERI_LT[1]*(1-t)+CORAL[1]*t);
            const blu=Math.round(PERI_LT[2]*(1-t)+CORAL[2]*t);
            ctx.fillStyle=`rgba(${red},${grn},${blu},0.92)`;
            ctx.fillRect(c*CELL+1,r*CELL+1,CELL-2,CELL-2);
          }
        }
        tint(ctx,W,H);
      };
    },

    /* ── ZONE 2: Slime mould — agents following pheromone trails ── */
    slime: function (canvas, ctx, W, H) {
      const N = 600;
      const SENSE = 18, SENSE_ANG = 0.42, TURN = 0.38, SPEED = 1.4;
      const DECAY = 0.97, DIFFUSE = 0.18;

      // Pheromone grid (downscaled for perf)
      const GS = 3;
      const GW = Math.floor(W / GS), GH = Math.floor(H / GS);
      let trail = new Float32Array(GW * GH);
      let tmp   = new Float32Array(GW * GH);

      const agents = Array.from({ length: N }, () => ({
        x: W / 2 + (Math.random() - 0.5) * W * 0.6,
        y: H / 2 + (Math.random() - 0.5) * H * 0.6,
        ang: Math.random() * Math.PI * 2,
      }));

      function sense(x, y, ang) {
        const sx = Math.round((x + Math.cos(ang) * SENSE) / GS);
        const sy = Math.round((y + Math.sin(ang) * SENSE) / GS);
        const cx = Math.max(0, Math.min(GW - 1, sx));
        const cy = Math.max(0, Math.min(GH - 1, sy));
        return trail[cy * GW + cx];
      }

      let frame = 0;
      let imgData = null;

      return function tick() {
        frame++;

        // Move agents
        for (const a of agents) {
          const fwd   = sense(a.x, a.y, a.ang);
          const left  = sense(a.x, a.y, a.ang - SENSE_ANG);
          const right = sense(a.x, a.y, a.ang + SENSE_ANG);
          if (fwd >= left && fwd >= right) { /* keep */ }
          else if (left > right) a.ang -= TURN + Math.random() * 0.1;
          else if (right > left) a.ang += TURN + Math.random() * 0.1;
          else a.ang += (Math.random() - 0.5) * 0.6;

          a.x += Math.cos(a.ang) * SPEED;
          a.y += Math.sin(a.ang) * SPEED;

          // Wrap
          if (a.x < 0) a.x += W; if (a.x >= W) a.x -= W;
          if (a.y < 0) a.y += H; if (a.y >= H) a.y -= H;

          // Deposit
          const gx = Math.floor(a.x / GS), gy = Math.floor(a.y / GS);
          if (gx >= 0 && gx < GW && gy >= 0 && gy < GH)
            trail[gy * GW + gx] = Math.min(1, trail[gy * GW + gx] + 0.4);
        }

        // Diffuse + decay
        if (frame % 2 === 0) {
          for (let y = 0; y < GH; y++) {
            for (let x = 0; x < GW; x++) {
              let s = 0, n = 0;
              for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
                const nx = (x + dx + GW) % GW, ny = (y + dy + GH) % GH;
                s += trail[ny * GW + nx]; n++;
              }
              tmp[y * GW + x] = (trail[y * GW + x] * (1 - DIFFUSE) + (s / n) * DIFFUSE) * DECAY;
            }
          }
          const swap = trail; trail = tmp; tmp = swap;
        }

        // Render
        if (!imgData) imgData = ctx.createImageData(W, H);
        const d = imgData.data;
        for (let py = 0; py < H; py++) {
          for (let px = 0; px < W; px++) {
            const gx = Math.floor(px / GS), gy = Math.floor(py / GS);
            const v = Math.min(1, trail[gy * GW + gx]);
            const i = (py * W + px) * 4;
            // Background: deep navy; trail: coral→periwinkle
            const br = Math.round(24 + v * (CORAL[0] - 24));
            const bg = Math.round(22 + v * (PERI[1] - 22 + 60));
            const bb = Math.round(53 + v * (PERI[2] - 53 + 30));
            d[i] = br; d[i+1] = bg; d[i+2] = bb; d[i+3] = 255;
          }
        }
        ctx.putImageData(imgData, 0, 0);
        tint(ctx, W, H);
      };
    },

    /* ── ZONE 3: Rotating clock / orrery ── */
    clock: function (canvas, ctx, W, H) {
      const cx = W / 2, cy = H / 2;
      const BASE_R = Math.min(W, H) * 0.38;

      // Gear-like rings
      const RINGS = [
        { r: BASE_R * 0.22, teeth: 8,  speed:  0.012, col: CORAL },
        { r: BASE_R * 0.45, teeth: 16, speed: -0.007, col: PERI },
        { r: BASE_R * 0.70, teeth: 28, speed:  0.004, col: PERI_LT },
        { r: BASE_R * 0.95, teeth: 40, speed: -0.0025,col: CORAL },
      ];
      // Clock hands
      const HANDS = [
        { len: BASE_R * 0.18, speed: 0.05,   width: 3, col: CORAL },    // second-ish
        { len: BASE_R * 0.34, speed: 0.008,  width: 2, col: PERI_LT },  // minute-ish
        { len: BASE_R * 0.24, speed: 0.0006, width: 4, col: PERI },     // hour-ish
      ];
      // Orbit dots (key historical figures)
      const DOTS = [
        { r: BASE_R * 0.55, speed: 0.009,  phase: 0,              size: 5 },
        { r: BASE_R * 0.55, speed: 0.009,  phase: Math.PI * 0.66, size: 5 },
        { r: BASE_R * 0.55, speed: 0.009,  phase: Math.PI * 1.33, size: 5 },
        { r: BASE_R * 0.80, speed: 0.005,  phase: 0.5,            size: 4 },
        { r: BASE_R * 0.80, speed: 0.005,  phase: 2.1,            size: 4 },
        { r: BASE_R * 0.80, speed: 0.005,  phase: 4.2,            size: 4 },
        { r: BASE_R * 0.80, speed: 0.005,  phase: 5.8,            size: 4 },
      ];

      let t = 0;

      function drawGear(r, teeth, angle) {
        const toothH = r * 0.12, toothW = (Math.PI * 2) / (teeth * 2);
        ctx.beginPath();
        for (let i = 0; i < teeth * 2; i++) {
          const a = angle + i * toothW;
          const outerR = i % 2 === 0 ? r + toothH : r;
          ctx.lineTo(cx + Math.cos(a) * outerR, cy + Math.sin(a) * outerR);
        }
        ctx.closePath();
      }

      return function tick() {
        t += 1;
        ctx.fillStyle = 'rgba(24,22,53,0.28)'; ctx.fillRect(0, 0, W, H);

        // Rings / gears
        for (const ring of RINGS) {
          const angle = t * ring.speed;
          drawGear(ring.r, ring.teeth, angle);
          ctx.strokeStyle = `rgba(${ring.col[0]},${ring.col[1]},${ring.col[2]},0.55)`;
          ctx.lineWidth = 1.5;
          ctx.stroke();

          // Inner circle
          ctx.beginPath();
          ctx.arc(cx, cy, ring.r * 0.88, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(${ring.col[0]},${ring.col[1]},${ring.col[2]},0.15)`;
          ctx.lineWidth = 1;
          ctx.stroke();
        }

        // Orbit dots
        for (const dot of DOTS) {
          const a = dot.phase + t * dot.speed;
          const x = cx + Math.cos(a) * dot.r;
          const y = cy + Math.sin(a) * dot.r;
          ctx.beginPath();
          ctx.arc(x, y, dot.size, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(${CORAL[0]},${CORAL[1]},${CORAL[2]},0.85)`;
          ctx.fill();
          // glow
          const grd = ctx.createRadialGradient(x, y, 0, x, y, dot.size * 3);
          grd.addColorStop(0, `rgba(${CORAL[0]},${CORAL[1]},${CORAL[2]},0.25)`);
          grd.addColorStop(1, 'rgba(0,0,0,0)');
          ctx.beginPath(); ctx.arc(x, y, dot.size * 3, 0, Math.PI * 2);
          ctx.fillStyle = grd; ctx.fill();
        }

        // Clock hands
        for (const hand of HANDS) {
          const a = t * hand.speed - Math.PI / 2;
          ctx.beginPath();
          ctx.moveTo(cx, cy);
          ctx.lineTo(cx + Math.cos(a) * hand.len, cy + Math.sin(a) * hand.len);
          ctx.strokeStyle = `rgba(${hand.col[0]},${hand.col[1]},${hand.col[2]},0.9)`;
          ctx.lineWidth = hand.width;
          ctx.lineCap = 'round';
          ctx.stroke();
        }

        // Centre cap
        ctx.beginPath(); ctx.arc(cx, cy, 6, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${CORAL[0]},${CORAL[1]},${CORAL[2]},1)`; ctx.fill();

        tint(ctx, W, H);
      };
    },

    /* ── ZONE 4: Dense Boids (500) ── */
    boids4: function (canvas, ctx, W, H) {
      const N = 500;
      const boids = Array.from({ length: N }, () => ({
        x: Math.random() * W, y: Math.random() * H,
        vx: (Math.random()-0.5)*2.8, vy: (Math.random()-0.5)*2.8,
        t: Math.random(),
      }));
      const SEP=22, ALI=50, COH=75, MS=2.8, MF=0.08;
      function lim(vx,vy,m){const s=Math.hypot(vx,vy);return s>m?[vx/s*m,vy/s*m]:[vx,vy];}

      return function tick(){
        for(let i=0;i<N;i++){
          const b=boids[i];
          let sx=0,sy=0,sn=0,ax=0,ay=0,an=0,cx=0,cy=0,cn=0;
          for(let j=0;j<N;j++){
            if(i===j)continue;
            const o=boids[j],dx=o.x-b.x,dy=o.y-b.y,d=Math.hypot(dx,dy);
            if(d<SEP&&d>0){sx-=dx/d;sy-=dy/d;sn++;}
            if(d<ALI){ax+=o.vx;ay+=o.vy;an++;}
            if(d<COH){cx+=o.x;cy+=o.y;cn++;}
          }
          let fx=0,fy=0;
          if(sn){const[lx,ly]=lim(sx/sn,sy/sn,MF);fx+=lx;fy+=ly;}
          if(an){const[lx,ly]=lim(ax/an-b.vx,ay/an-b.vy,MF);fx+=lx;fy+=ly;}
          if(cn){const[lx,ly]=lim(cx/cn-b.x,cy/cn-b.y,MF*0.5);fx+=lx;fy+=ly;}
          b.vx+=fx;b.vy+=fy;[b.vx,b.vy]=lim(b.vx,b.vy,MS);
          b.x=(b.x+b.vx+W)%W;b.y=(b.y+b.vy+H)%H;
        }
        ctx.fillStyle='rgba(24,22,53,0.22)';ctx.fillRect(0,0,W,H);
        for(const b of boids){
          const ang=Math.atan2(b.vy,b.vx);
          const r=Math.round(PERI_LT[0]*(1-b.t)+CORAL[0]*b.t);
          const g=Math.round(PERI_LT[1]*(1-b.t)+CORAL[1]*b.t);
          const bl=Math.round(PERI_LT[2]*(1-b.t)+CORAL[2]*b.t);
          ctx.save();ctx.translate(b.x,b.y);ctx.rotate(ang);
          ctx.beginPath();ctx.moveTo(6,0);ctx.lineTo(-4,2.5);ctx.lineTo(-4,-2.5);ctx.closePath();
          ctx.fillStyle=`rgba(${r},${g},${bl},0.85)`;ctx.fill();
          ctx.restore();
        }
        tint(ctx,W,H);
      };
    },

    /* ── ZONE 5: Growing phylogenetic tree ── */
    phylo: function (canvas, ctx, W, H) {
      // Branch data structure
      function newBranch(x, y, angle, length, depth, hue) {
        return { x, y, angle, length, depth, hue, grown: 0, children: [], spawned: false };
      }

      const MAX_DEPTH = 7;
      let roots = [];

      function init() {
        roots = [];
        // Start 2-3 root trees from bottom
        const nTrees = 3;
        for (let i = 0; i < nTrees; i++) {
          const rx = W * (0.2 + 0.3 * i);
          roots.push(newBranch(rx, H * 0.95, -Math.PI / 2, H * 0.14, 0, i / nTrees));
        }
      }
      init();

      function growBranch(b) {
        b.grown = Math.min(1, b.grown + 0.018 / (b.depth + 1));
        if (b.grown > 0.85 && !b.spawned && b.depth < MAX_DEPTH) {
          b.spawned = true;
          const nChildren = b.depth < 3 ? 2 : (Math.random() < 0.55 ? 2 : 1);
          const spread = 0.35 + b.depth * 0.06;
          for (let k = 0; k < nChildren; k++) {
            const angle = b.angle + (k === 0 ? -1 : 1) * spread * (0.7 + Math.random() * 0.6);
            const len = b.length * (0.6 + Math.random() * 0.25);
            const hue = b.hue + (Math.random() - 0.5) * 0.18;
            const tipX = b.x + Math.cos(b.angle) * b.length * b.grown;
            const tipY = b.y + Math.sin(b.angle) * b.length * b.grown;
            b.children.push(newBranch(tipX, tipY, angle, len, b.depth + 1, hue));
          }
        }
        for (const c of b.children) growBranch(c);
      }

      function drawBranch(b) {
        if (b.grown <= 0) return;
        const tipX = b.x + Math.cos(b.angle) * b.length * b.grown;
        const tipY = b.y + Math.sin(b.angle) * b.length * b.grown;
        const h = b.hue % 1;
        const r = Math.round(CORAL[0] * (1 - h) + PERI[0] * h);
        const g = Math.round(CORAL[1] * (1 - h) + PERI[1] * h);
        const bl = Math.round(CORAL[2] * (1 - h) + PERI[2] * h);
        const lw = Math.max(0.5, 3 - b.depth * 0.38);
        const alpha = Math.min(1, 0.55 + b.grown * 0.4);

        ctx.beginPath();
        ctx.moveTo(b.x, b.y);
        ctx.lineTo(tipX, tipY);
        ctx.strokeStyle = `rgba(${r},${g},${bl},${alpha})`;
        ctx.lineWidth = lw;
        ctx.lineCap = 'round';
        ctx.stroke();

        // Tip dot on terminal branches
        if (b.grown >= 1 && b.depth >= MAX_DEPTH - 1) {
          ctx.beginPath();
          ctx.arc(tipX, tipY, 2.5, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(${r},${g},${bl},0.9)`;
          ctx.fill();
        }

        for (const c of b.children) drawBranch(c);
      }

      let frame = 0;
      let resetTimer = 0;

      return function tick() {
        frame++;
        resetTimer++;

        // Periodically re-seed the tree for ongoing evolution feel
        if (resetTimer > 520) {
          init();
          resetTimer = 0;
        }

        ctx.fillStyle = 'rgba(24,22,53,0.18)'; ctx.fillRect(0, 0, W, H);

        for (const r of roots) {
          growBranch(r);
          drawBranch(r);
        }

        tint(ctx, W, H);
      };
    },

    /* ── ZONE 6: Rule 30 cellular automaton ── */
    rule30: function (canvas, ctx, W, H) {
      const CELL=6;
      const COLS=Math.floor(W/CELL), ROWS=Math.floor(H/CELL);
      const RULE=30;
      const lookup=Array.from({length:8},(_,i)=>(RULE>>i)&1);
      let buf=Array.from({length:ROWS},()=>new Uint8Array(COLS));
      let head=0;
      buf[0][Math.floor(COLS/2)]=1;
      let frame=0;

      function stepRow(){
        const prev=buf[(head-1+ROWS)%ROWS],cur=buf[head];
        cur.fill(0);
        for(let c=0;c<COLS;c++){
          const l=prev[(c-1+COLS)%COLS],m=prev[c],r=prev[(c+1)%COLS];
          cur[c]=lookup[l*4+m*2+r];
        }
        head=(head+1)%ROWS;
      }

      return function tick(){
        frame++;
        if(frame%3===0)stepRow();
        ctx.fillStyle='rgba(24,22,53,0.28)';ctx.fillRect(0,0,W,H);
        for(let r=0;r<ROWS;r++){
          const rowIdx=(head+r)%ROWS,row=buf[rowIdx];
          for(let c=0;c<COLS;c++){
            if(row[c]){
              const t2=c/COLS;
              const red=Math.round(PERI_LT[0]*(1-t2)+CORAL[0]*t2);
              const grn=Math.round(PERI_LT[1]*(1-t2)+CORAL[1]*t2);
              const blu=Math.round(PERI_LT[2]*(1-t2)+CORAL[2]*t2);
              const alpha=0.5+0.45*(r/ROWS);
              ctx.fillStyle=`rgba(${red},${grn},${blu},${alpha})`;
              ctx.fillRect(c*CELL,r*CELL,CELL-1,CELL-1);
            }
          }
        }
        tint(ctx,W,H);
      };
    },

    /* ── ZONE 7: Chemical/digital hybrid — The Matrix meets chemistry ── */
    matrix: function (canvas, ctx, W, H) {
      // Chemical formulae and code symbols mixed
      const SYMBOLS = [
        'C','H','O','N','P','S','ATP','DNA','RNA','H₂O','CO₂','NH₃',
        '01','10','00','11','{','}',' =>','+=','&&','||','∑','∂','λ',
        'Σ','α','β','γ','ψ','φ','→','⇌','≡','≈','∞','∇','∫',
        'CH₄','C₆H₁₂O₆','NaCl','O₂','N₂','Fe','Cu','Zn',
      ];

      const COL_W = 22;
      const COLS_N = Math.floor(W / COL_W);
      const columns = Array.from({ length: COLS_N }, () => ({
        y: Math.random() * H,
        speed: 0.8 + Math.random() * 2.2,
        symbols: Array.from({ length: 24 }, () => SYMBOLS[Math.floor(Math.random() * SYMBOLS.length)]),
        hue: Math.random(),
        len: 8 + Math.floor(Math.random() * 16),
        swapTimer: Math.floor(Math.random() * 40),
      }));

      let frame = 0;

      return function tick() {
        frame++;
        ctx.fillStyle = 'rgba(24,22,53,0.22)'; ctx.fillRect(0, 0, W, H);
        ctx.font = '13px "DM Mono", monospace';

        for (const col of columns) {
          col.y += col.speed;
          if (col.y > H + col.len * 18) {
            col.y = -col.len * 18;
            col.speed = 0.8 + Math.random() * 2.2;
            col.hue = Math.random();
          }
          col.swapTimer--;
          if (col.swapTimer <= 0) {
            const idx = Math.floor(Math.random() * col.symbols.length);
            col.symbols[idx] = SYMBOLS[Math.floor(Math.random() * SYMBOLS.length)];
            col.swapTimer = 10 + Math.floor(Math.random() * 30);
          }

          for (let i = 0; i < col.len; i++) {
            const sy = col.y - i * 18;
            if (sy < -18 || sy > H + 18) continue;
            const fade = 1 - (i / col.len);
            const isHead = (i === 0);
            const sym = col.symbols[i % col.symbols.length];

            const h = col.hue;
            const r = Math.round(CORAL[0] * (1 - h) + TEAL[0] * h);
            const g = Math.round(CORAL[1] * (1 - h) + TEAL[1] * h);
            const bl = Math.round(CORAL[2] * (1 - h) + TEAL[2] * h);

            if (isHead) {
              ctx.fillStyle = `rgba(255,255,255,${fade * 0.95})`;
            } else {
              ctx.fillStyle = `rgba(${r},${g},${bl},${fade * 0.85})`;
            }
            ctx.fillText(sym, col.y < 0 ? -1000 : col.symbols.length ? Math.floor(columns.indexOf(col) * COL_W) : 0,
              sy);
          }
        }

        // Fix: use column index for x
        ctx.clearRect(0, 0, W, H);
        ctx.fillStyle = 'rgba(24,22,53,0.22)'; ctx.fillRect(0, 0, W, H);
        for (let ci = 0; ci < columns.length; ci++) {
          const col = columns[ci];
          const x = ci * COL_W + 2;
          for (let i = 0; i < col.len; i++) {
            const sy = col.y - i * 18;
            if (sy < -18 || sy > H + 18) continue;
            const fade = 1 - (i / col.len);
            const isHead = (i === 0);
            const sym = col.symbols[i % col.symbols.length];
            const h = col.hue;
            const r = Math.round(CORAL[0] * (1 - h) + TEAL[0] * h);
            const g = Math.round(CORAL[1] * (1 - h) + TEAL[1] * h);
            const bl = Math.round(CORAL[2] * (1 - h) + TEAL[2] * h);
            if (isHead) {
              ctx.fillStyle = `rgba(220,240,255,${fade * 0.98})`;
            } else {
              ctx.fillStyle = `rgba(${r},${g},${bl},${fade * 0.88})`;
            }
            ctx.fillText(sym, x, sy);
          }
        }
        tint(ctx, W, H);
      };
    },

    /* ── ZONE 8: Growing forest / L-system trees ── */
    forest: function (canvas, ctx, W, H) {
      // Multiple L-system trees growing, swaying in wind
      function makeTree(rootX) {
        return {
          rootX,
          rootY: H,
          phase: Math.random() * Math.PI * 2,
          speed: 0.006 + Math.random() * 0.004,
          scale: 0.55 + Math.random() * 0.45,
          hue: Math.random(),
          age: Math.random() * 200, // stagger start ages
        };
      }

      const trees = Array.from({ length: 7 }, (_, i) => makeTree(W * (0.08 + i * 0.14)));

      function drawTree(tree, t) {
        const { rootX, rootY, phase, speed, scale, hue } = tree;
        const wind = Math.sin(t * speed + phase) * 0.04;
        const maxAge = 300;
        const treeAge = Math.min(tree.age, maxAge);
        const growFrac = treeAge / maxAge;

        function branch(x, y, angle, len, depth, maxDepth) {
          if (depth > maxDepth || len < 1.5) return;
          const reachDepth = growFrac * maxDepth;
          if (depth > reachDepth + 1) return;
          const localGrow = Math.min(1, Math.max(0, reachDepth - depth + 1));

          const tx = x + Math.cos(angle + wind * depth) * len * localGrow;
          const ty = y + Math.sin(angle + wind * depth) * len * localGrow;

          const h = (hue + depth * 0.07) % 1;
          const r = Math.round(CORAL[0] * (1 - h) + TEAL[0] * h);
          const g = Math.round(CORAL[1] * (1 - h) + TEAL[1] * h);
          const bl = Math.round(CORAL[2] * (1 - h) + TEAL[2] * h);
          const lw = Math.max(0.5, (maxDepth - depth + 1) * 0.9 * scale);

          ctx.beginPath();
          ctx.moveTo(x, y);
          ctx.lineTo(tx, ty);
          ctx.strokeStyle = `rgba(${r},${g},${bl},${0.55 + localGrow * 0.35})`;
          ctx.lineWidth = lw;
          ctx.lineCap = 'round';
          ctx.stroke();

          if (depth === maxDepth || len < 6) {
            // Leaf / blossom
            ctx.beginPath();
            ctx.arc(tx, ty, 2.5 * scale, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${PERI_LT[0]},${PERI_LT[1]},${PERI_LT[2]},${localGrow * 0.8})`;
            ctx.fill();
          }

          const split = 0.44 + depth * 0.015;
          branch(tx, ty, angle - split, len * 0.68, depth + 1, maxDepth);
          branch(tx, ty, angle + split * 0.85, len * 0.65, depth + 1, maxDepth);
          if (depth < 3) branch(tx, ty, angle + wind * 0.5, len * 0.55, depth + 2, maxDepth);
        }

        const trunkLen = H * 0.14 * scale;
        const maxDepth = 8;
        branch(rootX, rootY, -Math.PI / 2, trunkLen, 0, maxDepth);
      }

      let t = 0;

      return function tick() {
        t++;
        ctx.fillStyle = 'rgba(24,22,53,0.2)'; ctx.fillRect(0, 0, W, H);

        for (const tree of trees) {
          tree.age += 0.35;
          if (tree.age > 500) tree.age = 0; // regrow
          drawTree(tree, t);
        }

        tint(ctx, W, H);
      };
    },

    /* ── ZONE 9: Starfield + prominent DNA helices + particle burst ── */
    future: function (canvas, ctx, W, H) {
      const STARS = Array.from({ length: 180 }, () => ({
        x: Math.random() * W, y: Math.random() * H,
        r: 0.8 + Math.random() * 2.2,
        alpha: 0.4 + Math.random() * 0.6,
        twinkle: Math.random() * Math.PI * 2,
        speed: 0.02 + Math.random() * 0.04,
      }));

      // Helices — centred and prominent
      const HELIX_COUNT = 3;
      const helices = Array.from({ length: HELIX_COUNT }, (_, i) => ({
        cx: W * (0.2 + 0.3 * i),
        phase: (i / HELIX_COUNT) * Math.PI * 1.5,
        speed: 0.018 - i * 0.003,
        amp: Math.min(W * 0.08, 38) + i * 6,
      }));

      // Particle bursts from helix nodes
      const particles = [];
      function spawnParticle(x, y, col) {
        particles.push({
          x, y,
          vx: (Math.random() - 0.5) * 2.5,
          vy: -0.5 - Math.random() * 1.5,
          life: 1,
          col,
        });
      }

      let t = 0;

      return function tick() {
        t++;
        ctx.fillStyle = 'rgba(24,22,53,0.25)'; ctx.fillRect(0, 0, W, H);

        // Stars
        for (const s of STARS) {
          s.twinkle += s.speed;
          const a = s.alpha * (0.5 + 0.5 * Math.sin(s.twinkle));
          ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(220,210,255,${a})`; ctx.fill();
        }

        // Helices
        for (const h of helices) {
          const period = H * 0.55;
          for (let y = 0; y < H; y += 4) {
            const phase = (y / period) * Math.PI * 2 + t * h.speed + h.phase;
            const x1 = h.cx + Math.cos(phase) * h.amp;
            const x2 = h.cx + Math.cos(phase + Math.PI) * h.amp;
            const a = 0.55 + 0.35 * Math.abs(Math.cos(phase));

            ctx.beginPath(); ctx.arc(x1, y, 3, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${CORAL[0]},${CORAL[1]},${CORAL[2]},${a})`; ctx.fill();
            ctx.beginPath(); ctx.arc(x2, y, 3, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${PERI[0]},${PERI[1]},${PERI[2]},${a})`; ctx.fill();

            // Rungs every 20px
            if (Math.round(y) % 20 < 4) {
              ctx.beginPath(); ctx.moveTo(x1, y); ctx.lineTo(x2, y);
              ctx.strokeStyle = `rgba(${PERI_LT[0]},${PERI_LT[1]},${PERI_LT[2]},${a * 0.6})`;
              ctx.lineWidth = 1.5; ctx.stroke();
              // Spawn particle occasionally
              if (Math.random() < 0.04) spawnParticle(x1, y, CORAL);
              if (Math.random() < 0.04) spawnParticle(x2, y, PERI);
            }
          }
        }

        // Particles
        for (let i = particles.length - 1; i >= 0; i--) {
          const p = particles[i];
          p.life -= 0.025; p.x += p.vx; p.y += p.vy; p.vy += 0.04;
          if (p.life <= 0) { particles.splice(i, 1); continue; }
          ctx.beginPath(); ctx.arc(p.x, p.y, 2, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(${p.col[0]},${p.col[1]},${p.col[2]},${p.life * 0.8})`; ctx.fill();
        }

        tint(ctx, W, H);
      };
    },

  }; // end SIM

  // ── Boot ──────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', () => {
    const hero = document.querySelector('header.hero');
    if (!hero) return;
    const simKey = hero.dataset.heroBg;
    if (!simKey || !SIM[simKey]) return;

    const canvas = document.createElement('canvas');
    canvas.className = 'hero-canvas';
    hero.insertBefore(canvas, hero.firstChild);

    let W, H, raf, tick;

    function resize() {
      W = canvas.width  = hero.offsetWidth;
      H = canvas.height = hero.offsetHeight;
      if (raf) cancelAnimationFrame(raf);
      const ctx = canvas.getContext('2d');
      // Fill background colour before first frame
      ctx.fillStyle = '#181635';
      ctx.fillRect(0, 0, W, H);
      tick = SIM[simKey](canvas, ctx, W, H);
      loop();
    }

    function loop() {
      tick();
      raf = requestAnimationFrame(loop);
    }

    resize();
    window.addEventListener('resize', resize);

    document.addEventListener('visibilitychange', () => {
      if (document.hidden) { cancelAnimationFrame(raf); raf = null; }
      else { loop(); }
    });
  });

})();
