// Monkey TD Blast - Simple Tower Defense Game
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

// --- UI State ---
let selectedMap = null;
const maps = [
    // Classic
    [
        {x: 0, y: 250}, {x: 200, y: 250}, {x: 200, y: 100}, {x: 600, y: 100}, {x: 600, y: 400}, {x: 800, y: 400}
    ],
    // Curvy
    [
        {x: 0, y: 400}, {x: 150, y: 400}, {x: 200, y: 200}, {x: 400, y: 200}, {x: 600, y: 350}, {x: 800, y: 350}
    ]
];

function selectMap(idx) {
    selectedMap = idx;
    document.getElementById('play-btn').disabled = false;
}

function startGame() {
    document.getElementById('map-select').style.display = 'none';
    document.getElementById('game-ui').style.display = '';
    resetGame();
}

function resetGame() {
    money = 500;
    selectedTower = null;
    towers = [];
    enemies = [];
    round = 1;
    lives = 20;
    enemySpeed = 1;
    enemyHealth = 10;
    spawnTimer = 0;
    path = maps[selectedMap || 0];
    updateUI();
    gameLoop();
}

// --- Tower Types ---
const towerTypes = {
    dart: {cost: 100, range: 90, dmg: 5, rate: 40, color: '#8d5524'},
    sniper: {cost: 200, range: 300, dmg: 10, rate: 80, color: '#607d8b'},
    cannon: {cost: 300, range: 100, dmg: 20, rate: 100, color: '#bdb76b', splash: true}
};

function selectTower(type) {
    selectedTower = type;
    // Highlight selected button
    document.querySelectorAll('.monkey-btn').forEach(btn => btn.classList.remove('selected'));
    const idx = ['dart','sniper','cannon'].indexOf(type);
    if (idx >= 0) document.querySelectorAll('.monkey-btn')[idx].classList.add('selected');
}

canvas.addEventListener('click', (e) => {
    if (!selectedTower) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    let t = towerTypes[selectedTower];
    if (money >= t.cost) {
        towers.push({x, y, type: selectedTower, cooldown: 0});
        money -= t.cost;
        updateUI();
    }
});

function updateUI() {
    document.getElementById('money').textContent = `💰 $${money}`;
    document.getElementById('lives').textContent = `❤️ ${lives}`;
    document.getElementById('round').textContent = `Round ${round}`;
}

function updateTowers() {
    for (let tower of towers) {
        tower.cooldown--;
        let t = towerTypes[tower.type];
        if (tower.cooldown <= 0) {
            let targets = enemies.filter(e => Math.hypot(e.x - tower.x, e.y - tower.y) < t.range);
            if (targets.length) {
                if (t.splash) {
                    for (let e of targets) e.health -= t.dmg;
                } else {
                    targets[0].health -= t.dmg;
                }
                tower.cooldown = t.rate;
            }
        }
    }
    // Remove dead enemies, give money
    for (let i = enemies.length - 1; i >= 0; i--) {
        if (enemies[i].health <= 0) {
            money += 10;
            enemies.splice(i, 1);
            updateUI();
        }
    }
}

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    // Draw path
    ctx.strokeStyle = '#e0c000';
    ctx.lineWidth = 16;
    ctx.beginPath();
    ctx.moveTo(path[0].x, path[0].y);
    for (let p of path) ctx.lineTo(p.x, p.y);
    ctx.stroke();
    // Draw towers
    for (let tower of towers) {
        ctx.beginPath();
        ctx.arc(tower.x, tower.y, 18, 0, 2 * Math.PI);
        ctx.fillStyle = towerTypes[tower.type].color;
        ctx.fill();
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 2;
        ctx.stroke();
    }
    // Draw enemies (bloons/monkeys)
    for (let enemy of enemies) {
        ctx.beginPath();
        ctx.arc(enemy.x, enemy.y, 14, 0, 2 * Math.PI);
        ctx.fillStyle = '#ff4d4d';
        ctx.fill();
        ctx.strokeStyle = '#a00';
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.fillStyle = '#fff';
        ctx.font = '12px Arial';
        ctx.fillText(enemy.health, enemy.x - 8, enemy.y + 4);
    }
    // Draw lives/round
    ctx.fillStyle = '#fff';
    ctx.font = '18px Arial';
    ctx.fillText(`Lives: ${lives}  Round: ${round}`, 10, 30);
}

function gameLoop() {
    if (lives <= 0) {
        ctx.fillStyle = '#f00';
        ctx.font = '48px Arial';
        ctx.fillText('Game Over!', 300, 250);
        return;
    }
    spawnTimer--;
    if (spawnTimer <= 0) {
        spawnEnemy();
        spawnTimer = Math.max(30 - round * 2, 10);
    }
    updateEnemies();
    updateTowers();
    draw();
    // Next round
    if (enemies.length === 0 && spawnTimer < 0) {
        round++;
        enemyHealth += 5;
        enemySpeed += 0.1;
        spawnTimer = 60;
    }
    requestAnimationFrame(gameLoop);
}

function spawnEnemy() {
    enemies.push({x: path[0].x, y: path[0].y, pathIndex: 0, t: 0, health: enemyHealth});
}

function updateEnemies() {
    for (let enemy of enemies) {
        let next = path[enemy.pathIndex + 1];
        if (!next) continue;
        let dx = next.x - enemy.x;
        let dy = next.y - enemy.y;
        let dist = Math.sqrt(dx*dx + dy*dy);
        if (dist < enemySpeed) {
            enemy.x = next.x;
            enemy.y = next.y;
            enemy.pathIndex++;
        } else {
            enemy.x += (dx / dist) * enemySpeed;
            enemy.y += (dy / dist) * enemySpeed;
        }
    }
    // Remove enemies that reach the end
    for (let i = enemies.length - 1; i >= 0; i--) {
        if (enemies[i].pathIndex >= path.length - 1) {
            lives--;
            enemies.splice(i, 1);
            updateUI();
        }
    }
}

// --- Start on map select ---
document.getElementById('game-ui').style.display = 'none';
document.getElementById('map-select').style.display = '';
