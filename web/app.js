const MILESTONES = [128, 256, 512, 1024, 2048, 4096];
const TILE_COLORS = {
  0: "#d4c1a7",
  2: "#f7ecdc",
  4: "#f2e1c5",
  8: "#efbf84",
  16: "#e69f61",
  32: "#df7f58",
  64: "#d66245",
  128: "#e5c065",
  256: "#ddb457",
  512: "#d6a748",
  1024: "#ce9a3a",
  2048: "#c68d2e"
};

function hashString(input) {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < input.length; i += 1) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

class RNG {
  constructor(seedValue = Date.now()) {
    this.state = seedValue >>> 0;
    if (!this.state) this.state = 0x12345678;
  }

  nextInt() {
    this.state = (Math.imul(this.state, 1664525) + 1013904223) >>> 0;
    return this.state;
  }

  random() {
    return this.nextInt() / 4294967296;
  }

  choice(list) {
    return list[Math.floor(this.random() * list.length)];
  }

  sample(list, count) {
    const arr = list.slice();
    const out = [];
    for (let i = 0; i < count; i += 1) {
      const idx = Math.floor(this.random() * arr.length);
      out.push(arr[idx]);
      arr.splice(idx, 1);
    }
    return out;
  }

  getState() {
    return this.state >>> 0;
  }

  setState(state) {
    this.state = state >>> 0;
  }
}

class Remix2048Web {
  constructor() {
    this.refs = {
      score: document.getElementById("score"),
      combo: document.getElementById("combo"),
      steps: document.getElementById("steps"),
      best: document.getElementById("best"),
      gridSize: document.getElementById("gridSize"),
      mode: document.getElementById("mode"),
      board: document.getElementById("board"),
      tasks: document.getElementById("tasks"),
      toolStatus: document.getElementById("toolStatus"),
      modeStatus: document.getElementById("modeStatus"),
      pauseMask: document.getElementById("pauseMask"),
      toast: document.getElementById("toast"),
      restartBtn: document.getElementById("restartBtn"),
      undoBtn: document.getElementById("undoBtn"),
      pauseBtn: document.getElementById("pauseBtn"),
      muteBtn: document.getElementById("muteBtn"),
      installBtn: document.getElementById("installBtn"),
      hammerBtn: document.getElementById("hammerBtn"),
      freezeBtn: document.getElementById("freezeBtn"),
      themeBtn: document.getElementById("themeBtn"),
      dailyBoard: document.getElementById("dailyBoard"),
      allTimeBoard: document.getElementById("allTimeBoard"),
      playerName: document.getElementById("playerName"),
      cloudStatus: document.getElementById("cloudStatus")
    };

    this.themes = ["classic", "ocean", "forest", "sunset"];
    this.themeIndex = 0;

    this.size = 4;
    this.grid = [];
    this.score = 0;
    this.bestScore = Number(localStorage.getItem("remix2048_best") || 0);
    this.comboStreak = 0;
    this.maxComboStreak = 0;
    this.maxTile = 0;
    this.stepsTaken = 0;
    this.bestMoveScore = 0;
    this.bestMoveTurn = 0;
    this.lastComboMultiplier = 1;
    this.gameOver = false;
    this.isPaused = false;
    this.isMuted = false;
    this.isAnimating = false;

    this.modeName = "Classic";
    this.timeLimit = 120;
    this.remainingTime = this.timeLimit;
    this.stepsLimit = 30;
    this.timerId = null;
    this.dailySeed = null;

    this.tasks = [];
    this.tasksCompleted = 0;

    this.hammerUses = 2;
    this.freezeUses = 2;
    this.selectedTool = null;
    this.frozenCells = {};

    this.lastState = null;
    this.milestonesReached = new Set();

    this.rng = new RNG();
    this.deferredInstallPrompt = null;
    this.apiBase = this.resolveApiBase();
    this.cloudReachable = false;
    this.lastCloudFetchAt = 0;
    this.onlineDailyBoard = [];
    this.onlineAllTimeBoard = [];
    this.playerName = localStorage.getItem("remix2048_player_name") || "Player";
    this.clientId = this.getOrCreateClientId();

    this.touchStart = null;

    this.refs.playerName.value = this.playerName;
    this.bindEvents();
    this.bindInstallPrompt();
    this.restartGame();
  }

  bindEvents() {
    this.refs.gridSize.addEventListener("change", () => this.changeSize());
    this.refs.mode.addEventListener("change", () => this.changeMode());

    this.refs.restartBtn.addEventListener("click", () => this.restartGame());
    this.refs.undoBtn.addEventListener("click", () => this.undoMove());
    this.refs.pauseBtn.addEventListener("click", () => this.togglePause());
    this.refs.muteBtn.addEventListener("click", () => this.toggleMute());
    this.refs.hammerBtn.addEventListener("click", () => this.activateHammer());
    this.refs.freezeBtn.addEventListener("click", () => this.activateFreeze());
    this.refs.themeBtn.addEventListener("click", () => this.rotateTheme());
    this.refs.installBtn.addEventListener("click", () => this.installApp());
    this.refs.playerName.addEventListener("change", () => this.updatePlayerName());
    this.refs.playerName.addEventListener("blur", () => this.updatePlayerName());

    window.addEventListener("keydown", (event) => {
      if (this.gameOver) return;
      const key = event.key.toLowerCase();
      if (["arrowup", "arrowdown", "arrowleft", "arrowright", "h", "f", "u", "r", "p", "m"].includes(key)) {
        event.preventDefault();
      }
      if (key === "arrowup") this.move("up");
      if (key === "arrowdown") this.move("down");
      if (key === "arrowleft") this.move("left");
      if (key === "arrowright") this.move("right");
      if (key === "h") this.activateHammer();
      if (key === "f") this.activateFreeze();
      if (key === "u") this.undoMove();
      if (key === "r") this.restartGame();
      if (key === "p") this.togglePause();
      if (key === "m") this.toggleMute();
    });

    this.refs.board.addEventListener("touchstart", (event) => {
      const touch = event.changedTouches[0];
      this.touchStart = { x: touch.clientX, y: touch.clientY };
    }, { passive: true });

    this.refs.board.addEventListener("touchend", (event) => {
      if (!this.touchStart) return;
      const touch = event.changedTouches[0];
      const dx = touch.clientX - this.touchStart.x;
      const dy = touch.clientY - this.touchStart.y;
      this.touchStart = null;

      if (Math.abs(dx) < 28 && Math.abs(dy) < 28) return;
      if (Math.abs(dx) > Math.abs(dy)) {
        this.move(dx > 0 ? "right" : "left");
      } else {
        this.move(dy > 0 ? "down" : "up");
      }
    }, { passive: true });
  }

  updatePlayerName() {
    const cleaned = (this.refs.playerName.value || "").trim().slice(0, 18);
    this.playerName = cleaned || "Player";
    this.refs.playerName.value = this.playerName;
    localStorage.setItem("remix2048_player_name", this.playerName);
  }

  getOrCreateClientId() {
    const key = "remix2048_client_id";
    const existing = localStorage.getItem(key);
    if (existing) return existing;

    let randomPart = "";
    if (window.crypto && typeof window.crypto.randomUUID === "function") {
      randomPart = window.crypto.randomUUID();
    } else {
      randomPart = `${Date.now()}-${Math.floor(Math.random() * 0xffffffff).toString(16)}`;
    }

    const id = `web-${hashString(randomPart).toString(16)}`;
    localStorage.setItem(key, id);
    return id;
  }

  resolveApiBase() {
    const fromQuery = new URLSearchParams(window.location.search).get("api");
    const fromStorage = localStorage.getItem("remix2048_api_base");
    const fromGlobal = window.REMIX2048_API_BASE;
    const picked = (fromQuery || fromStorage || fromGlobal || "http://localhost:8787/api").trim();
    const normalized = picked.replace(/\/$/, "");

    if (fromQuery) {
      localStorage.setItem("remix2048_api_base", normalized);
    }

    return normalized;
  }

  setCloudStatus(message, ok = false) {
    this.refs.cloudStatus.textContent = `Cloud: ${message}`;
    this.refs.cloudStatus.style.color = ok ? "#2f8f57" : "#7a4f41";
  }

  bindInstallPrompt() {
    window.addEventListener("beforeinstallprompt", (event) => {
      event.preventDefault();
      this.deferredInstallPrompt = event;
      this.refs.installBtn.classList.remove("hidden");
    });

    window.addEventListener("appinstalled", () => {
      this.deferredInstallPrompt = null;
      this.refs.installBtn.classList.add("hidden");
    });
  }

  async installApp() {
    if (!this.deferredInstallPrompt) {
      this.toast("Install not available in this browser now");
      return;
    }

    this.deferredInstallPrompt.prompt();
    const outcome = await this.deferredInstallPrompt.userChoice;
    if (outcome.outcome === "accepted") {
      this.toast("Install started");
    }
    this.deferredInstallPrompt = null;
    this.refs.installBtn.classList.add("hidden");
  }

  rotateTheme() {
    this.themeIndex = (this.themeIndex + 1) % this.themes.length;
    const name = this.themes[this.themeIndex];
    const root = document.documentElement;
    const map = {
      classic: ["#f8f2e7", "#e8dac1", "#2f2216", "#6d5a46", "#d8613c"],
      ocean: ["#e6f2f6", "#cde1ea", "#1e3a4a", "#4b6c7d", "#2a84a0"],
      forest: ["#edf4ea", "#d6e3cf", "#253828", "#4f6452", "#4c8a4a"],
      sunset: ["#f9eee7", "#f0d7c8", "#43231a", "#7a4f41", "#c45f40"]
    };
    const [bg0, bg1, ink, inkSoft, accent] = map[name];
    root.style.setProperty("--bg0", bg0);
    root.style.setProperty("--bg1", bg1);
    root.style.setProperty("--ink", ink);
    root.style.setProperty("--ink-soft", inkSoft);
    root.style.setProperty("--accent", accent);
  }

  makeDailySeed() {
    const d = new Date();
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return Number(`${y}${m}${day}`);
  }

  resetRng() {
    if (this.modeName === "Daily") {
      this.dailySeed = this.makeDailySeed();
      this.rng = new RNG(hashString(`daily-${this.dailySeed}-size-${this.size}`));
    } else {
      this.dailySeed = null;
      this.rng = new RNG(Date.now() ^ Math.floor(Math.random() * 0xffffffff));
    }
  }

  restartGame() {
    this.stopTimer();

    const selectedSize = Number(this.refs.gridSize.value);
    this.size = this.modeName === "Daily" ? 4 : selectedSize;
    if (this.modeName === "Daily") this.refs.gridSize.value = "4";

    this.grid = Array.from({ length: this.size }, () => Array(this.size).fill(0));
    this.score = 0;
    this.comboStreak = 0;
    this.maxComboStreak = 0;
    this.maxTile = 0;
    this.stepsTaken = 0;
    this.bestMoveScore = 0;
    this.bestMoveTurn = 0;
    this.lastComboMultiplier = 1;
    this.gameOver = false;
    this.isPaused = false;
    this.isAnimating = false;
    this.tasksCompleted = 0;
    this.hammerUses = 2;
    this.freezeUses = 2;
    this.selectedTool = null;
    this.frozenCells = {};
    this.lastState = null;
    this.milestonesReached.clear();

    this.remainingTime = this.timeLimit;

    this.resetRng();
    this.generateTasks();
    this.spawnNewTile();
    this.spawnNewTile();

    if (this.modeName === "Timed") this.startTimer();

    this.createBoard();
    this.renderAll();
    this.refreshOnlineLeaderboards(true);
  }

  changeSize() {
    this.restartGame();
  }

  changeMode() {
    this.modeName = this.refs.mode.value;
    if (this.modeName === "Daily") {
      this.size = 4;
      this.refs.gridSize.value = "4";
    }
    this.restartGame();
  }

  getComboMultiplier() {
    return Math.min(2.5, 1 + this.comboStreak * 0.2);
  }

  createBoard() {
    this.refs.board.style.gridTemplateColumns = `repeat(${this.size}, 1fr)`;
    this.refs.board.innerHTML = "";
    for (let r = 0; r < this.size; r += 1) {
      for (let c = 0; c < this.size; c += 1) {
        const cell = document.createElement("button");
        cell.className = "cell";
        cell.type = "button";
        cell.dataset.row = String(r);
        cell.dataset.col = String(c);
        cell.addEventListener("click", () => this.onCellClick(r, c));
        this.refs.board.appendChild(cell);
      }
    }
  }

  getCellNode(r, c) {
    const index = r * this.size + c;
    return this.refs.board.children[index];
  }

  keyForPos(r, c) {
    return `${r},${c}`;
  }

  isFrozen(r, c) {
    return this.frozenCells[this.keyForPos(r, c)] !== undefined;
  }

  spawnNewTile() {
    const empty = [];
    for (let r = 0; r < this.size; r += 1) {
      for (let c = 0; c < this.size; c += 1) {
        if (this.grid[r][c] === 0 && !this.isFrozen(r, c)) empty.push([r, c]);
      }
    }
    if (!empty.length) return null;
    const [r, c] = this.rng.choice(empty);
    this.grid[r][c] = this.rng.random() < 0.9 ? 2 : 4;
    return [r, c];
  }

  processSegment(segment) {
    const arr = segment.filter((v) => v !== 0);
    while (arr.length < segment.length) arr.push(0);

    let gained = 0;
    let mergedCount = 0;
    for (let i = 0; i < arr.length - 1; i += 1) {
      if (arr[i] !== 0 && arr[i] === arr[i + 1]) {
        arr[i] *= 2;
        gained += arr[i];
        mergedCount += 1;
        arr[i + 1] = 0;
      }
    }

    const final = arr.filter((v) => v !== 0);
    while (final.length < segment.length) final.push(0);

    return { final, gained, mergedCount };
  }

  processLineWithLocks(lineValues, lockMask) {
    const result = lineValues.slice();
    let gained = 0;
    let merged = 0;

    let start = 0;
    while (start < lineValues.length) {
      if (lockMask[start]) {
        start += 1;
        continue;
      }

      let end = start;
      while (end < lineValues.length && !lockMask[end]) end += 1;

      const seg = lineValues.slice(start, end);
      const out = this.processSegment(seg);
      for (let i = start; i < end; i += 1) {
        result[i] = out.final[i - start];
      }
      gained += out.gained;
      merged += out.mergedCount;
      start = end;
    }

    return {
      result,
      moved: result.some((v, idx) => v !== lineValues[idx]),
      gained,
      merged
    };
  }

  buildMove(direction) {
    let moved = false;
    let mergeHappened = false;
    let moveBaseScore = 0;
    let mergedInMove = 0;

    const newGrid = this.grid.map((row) => row.slice());

    if (direction === "left" || direction === "right") {
      for (let r = 0; r < this.size; r += 1) {
        const row = this.grid[r].slice();
        let line = row;
        let lockMask = [];

        if (direction === "left") {
          lockMask = row.map((_, c) => this.isFrozen(r, c));
        } else {
          line = row.slice().reverse();
          lockMask = row.map((_, i) => this.isFrozen(r, this.size - 1 - i));
        }

        const out = this.processLineWithLocks(line, lockMask);
        const final = direction === "left" ? out.result : out.result.slice().reverse();

        newGrid[r] = final;
        moveBaseScore += out.gained;
        mergedInMove += out.merged;
        if (out.merged > 0) mergeHappened = true;
        if (final.some((v, i) => v !== this.grid[r][i])) moved = true;
      }
    } else {
      for (let c = 0; c < this.size; c += 1) {
        const col = this.grid.map((row) => row[c]);
        let line = col;
        let lockMask = [];

        if (direction === "up") {
          lockMask = col.map((_, r) => this.isFrozen(r, c));
        } else {
          line = col.slice().reverse();
          lockMask = col.map((_, i) => this.isFrozen(this.size - 1 - i, c));
        }

        const out = this.processLineWithLocks(line, lockMask);
        const final = direction === "up" ? out.result : out.result.slice().reverse();

        for (let r = 0; r < this.size; r += 1) {
          newGrid[r][c] = final[r];
        }

        moveBaseScore += out.gained;
        mergedInMove += out.merged;
        if (out.merged > 0) mergeHappened = true;
        if (final.some((v, i) => v !== col[i])) moved = true;
      }
    }

    return { newGrid, moved, mergeHappened, moveBaseScore, mergedInMove };
  }

  tickFrozenCells() {
    const next = {};
    Object.entries(this.frozenCells).forEach(([key, turns]) => {
      if (turns - 1 > 0) next[key] = turns - 1;
    });
    this.frozenCells = next;
  }

  canMoveDirection(dir) {
    return this.buildMove(dir).moved;
  }

  checkGameOver() {
    for (let r = 0; r < this.size; r += 1) {
      for (let c = 0; c < this.size; c += 1) {
        if (this.grid[r][c] === 0 && !this.isFrozen(r, c)) return false;
      }
    }
    return !["left", "right", "up", "down"].some((d) => this.canMoveDirection(d));
  }

  buildTaskPool() {
    return [
      {
        type: "tile_in_steps",
        target_tile: this.rng.choice([64, 128, 256]),
        max_steps: this.rng.choice([8, 10, 12]),
        reward: this.rng.choice([180, 220, 260]),
        done: false,
        failed: false
      },
      {
        type: "double_merge_total",
        target: this.rng.choice([2, 3, 4]),
        progress: 0,
        reward: this.rng.choice([200, 240, 280]),
        done: false,
        failed: false
      },
      {
        type: "reach_score",
        target_score: this.rng.choice([900, 1200, 1600]),
        reward: this.rng.choice([150, 200, 250]),
        done: false,
        failed: false
      }
    ];
  }

  generateTasks() {
    const pool = this.buildTaskPool();
    this.tasks = this.rng.sample(pool, this.rng.choice([1, 2]));
  }

  taskText(task) {
    if (task.type === "tile_in_steps") return `Reach ${task.target_tile} in ${task.max_steps} steps`;
    if (task.type === "double_merge_total") return `Trigger ${task.target} double-merges (${task.progress}/${task.target})`;
    if (task.type === "reach_score") return `Reach score ${task.target_score}`;
    return "Unknown task";
  }

  taskStatus(task) {
    if (task.done) return "done";
    if (task.failed) return "failed";
    return "running";
  }

  completeTask(task) {
    task.done = true;
    this.tasksCompleted += 1;
    this.score += task.reward;
    this.toast(`Task complete +${task.reward}`);
  }

  evaluateTasks(highestTile, mergedCount) {
    this.tasks.forEach((task) => {
      if (task.done || task.failed) return;
      if (task.type === "tile_in_steps") {
        if (highestTile >= task.target_tile && this.stepsTaken <= task.max_steps) this.completeTask(task);
        else if (this.stepsTaken > task.max_steps) task.failed = true;
      }
      if (task.type === "double_merge_total") {
        if (mergedCount >= 2) task.progress += 1;
        if (task.progress >= task.target) this.completeTask(task);
      }
      if (task.type === "reach_score") {
        if (this.score >= task.target_score) this.completeTask(task);
      }
    });
  }

  snapshotState() {
    return {
      grid: this.grid.map((r) => r.slice()),
      score: this.score,
      comboStreak: this.comboStreak,
      gameOver: this.gameOver,
      maxTile: this.maxTile,
      maxComboStreak: this.maxComboStreak,
      stepsTaken: this.stepsTaken,
      bestMoveScore: this.bestMoveScore,
      bestMoveTurn: this.bestMoveTurn,
      modeName: this.modeName,
      remainingTime: this.remainingTime,
      tasks: JSON.parse(JSON.stringify(this.tasks)),
      tasksCompleted: this.tasksCompleted,
      hammerUses: this.hammerUses,
      freezeUses: this.freezeUses,
      selectedTool: this.selectedTool,
      frozenCells: { ...this.frozenCells },
      dailySeed: this.dailySeed,
      rngState: this.rng.getState(),
      milestonesReached: Array.from(this.milestonesReached)
    };
  }

  restoreState(s) {
    this.grid = s.grid.map((r) => r.slice());
    this.score = s.score;
    this.comboStreak = s.comboStreak;
    this.gameOver = s.gameOver;
    this.maxTile = s.maxTile;
    this.maxComboStreak = s.maxComboStreak;
    this.stepsTaken = s.stepsTaken;
    this.bestMoveScore = s.bestMoveScore;
    this.bestMoveTurn = s.bestMoveTurn;
    this.modeName = s.modeName;
    this.refs.mode.value = s.modeName;
    this.remainingTime = s.remainingTime;
    this.tasks = JSON.parse(JSON.stringify(s.tasks));
    this.tasksCompleted = s.tasksCompleted;
    this.hammerUses = s.hammerUses;
    this.freezeUses = s.freezeUses;
    this.selectedTool = s.selectedTool;
    this.frozenCells = { ...s.frozenCells };
    this.dailySeed = s.dailySeed;
    this.rng.setState(s.rngState);
    this.milestonesReached = new Set(s.milestonesReached || []);
  }

  applyMoveResults(move, previousState) {
    if (!move.moved) return;

    this.lastState = previousState;
    const previousGrid = previousState.grid.map((r) => r.slice());

    this.grid = move.newGrid.map((r) => r.slice());
    this.stepsTaken += 1;

    let comboBonus = 0;
    if (move.mergeHappened) {
      this.comboStreak += 1;
      comboBonus = Math.floor(move.moveBaseScore * (this.getComboMultiplier() - 1));
    } else {
      this.comboStreak = 0;
    }

    this.maxComboStreak = Math.max(this.maxComboStreak, this.comboStreak);
    const gainedTotal = move.moveBaseScore + comboBonus;
    this.score += gainedTotal;

    if (gainedTotal > this.bestMoveScore) {
      this.bestMoveScore = gainedTotal;
      this.bestMoveTurn = this.stepsTaken;
    }

    const highestTile = Math.max(...this.grid.flat());
    this.evaluateTasks(highestTile, move.mergedInMove);

    if (this.modeName === "Steps" && this.stepsTaken >= this.stepsLimit) {
      this.renderAll();
      this.endGame("Step limit reached");
      return;
    }

    this.tickFrozenCells();
    const spawned = this.spawnNewTile();
    this.renderAll();
    this.animateMoveFeedback(previousGrid, this.grid, spawned);

    if (gainedTotal > 0) {
      const comboText = comboBonus > 0 ? ` (Combo +${comboBonus})` : "";
      this.toast(`+${gainedTotal}${comboText}`);
    }
  }

  move(direction) {
    if (this.gameOver || this.isAnimating || this.isPaused) return;
    const previous = this.snapshotState();
    const move = this.buildMove(direction);
    this.applyMoveResults(move, previous);
  }

  activateHammer() {
    if (this.gameOver || this.isPaused || this.isAnimating || this.hammerUses <= 0) return;
    this.selectedTool = this.selectedTool === "hammer" ? null : "hammer";
    this.renderTools();
  }

  activateFreeze() {
    if (this.gameOver || this.isPaused || this.isAnimating || this.freezeUses <= 0) return;
    this.selectedTool = this.selectedTool === "freeze" ? null : "freeze";
    this.renderTools();
  }

  onCellClick(r, c) {
    if (this.gameOver || this.isPaused || this.isAnimating) return;
    if (this.selectedTool === "hammer") this.useHammer(r, c);
    if (this.selectedTool === "freeze") this.useFreeze(r, c);
  }

  useHammer(r, c) {
    if (this.hammerUses <= 0) return;
    if (this.isFrozen(r, c)) {
      this.selectedTool = null;
      this.renderTools();
      this.toast("Frozen tile cannot be broken now");
      return;
    }
    if (this.grid[r][c] === 0) {
      this.selectedTool = null;
      this.renderTools();
      return;
    }
    this.lastState = this.snapshotState();
    this.grid[r][c] = 0;
    this.hammerUses -= 1;
    this.selectedTool = null;
    this.renderAll();
  }

  useFreeze(r, c) {
    if (this.freezeUses <= 0) return;
    if (this.grid[r][c] === 0) {
      this.selectedTool = null;
      this.renderTools();
      this.toast("Pick a non-empty tile to freeze");
      return;
    }
    if (this.isFrozen(r, c)) {
      this.selectedTool = null;
      this.renderTools();
      return;
    }
    this.lastState = this.snapshotState();
    this.frozenCells[this.keyForPos(r, c)] = 3;
    this.freezeUses -= 1;
    this.selectedTool = null;
    this.renderAll();
  }

  undoMove() {
    if (!this.lastState || this.isPaused || this.isAnimating) return;
    this.restoreState(this.lastState);
    this.lastState = null;
    if (this.modeName === "Timed") {
      this.stopTimer();
      this.startTimer();
    }
    this.renderAll();
  }

  togglePause() {
    if (this.gameOver || this.isAnimating) return;
    this.isPaused = !this.isPaused;
    if (this.isPaused) this.stopTimer();
    else if (this.modeName === "Timed") this.startTimer();
    this.renderTools();
    this.renderModeStatus();
    this.refs.pauseMask.classList.toggle("hidden", !this.isPaused);
  }

  toggleMute() {
    this.isMuted = !this.isMuted;
    this.renderTools();
  }

  startTimer() {
    this.stopTimer();
    this.timerId = setInterval(() => {
      if (this.gameOver || this.modeName !== "Timed" || this.isPaused) {
        this.stopTimer();
        return;
      }
      this.remainingTime -= 1;
      if (this.remainingTime <= 0) {
        this.remainingTime = 0;
        this.renderModeStatus();
        this.endGame("Time is up");
        return;
      }
      this.renderModeStatus();
    }, 1000);
  }

  stopTimer() {
    if (!this.timerId) return;
    clearInterval(this.timerId);
    this.timerId = null;
  }

  checkMilestones() {
    const highest = Math.max(...this.grid.flat());
    if (highest > this.maxTile) this.maxTile = highest;

    MILESTONES.forEach((m) => {
      if (highest >= m && !this.milestonesReached.has(m)) {
        this.milestonesReached.add(m);
        this.toast(`Milestone reached: ${m}`);
      }
    });
  }

  endGame(reason = "") {
    if (this.gameOver) return;
    this.gameOver = true;
    this.isPaused = false;
    this.refs.pauseMask.classList.add("hidden");
    this.stopTimer();

    this.bestScore = Math.max(this.bestScore, this.score);
    localStorage.setItem("remix2048_best", String(this.bestScore));
    this.recordLeaderboardResult();
    this.refreshOnlineLeaderboards(true);

    this.renderAll();

    const summary = [
      reason,
      `Final Score: ${this.score}`,
      `Highest Tile: ${this.maxTile}`,
      `Max Combo: x${(1 + Math.min(this.maxComboStreak, 7) * 0.2).toFixed(1)}`,
      `Steps: ${this.stepsTaken}`,
      `Best Move: +${this.bestMoveScore} (Turn ${this.bestMoveTurn})`,
      `Tasks Completed: ${this.tasksCompleted}/${this.tasks.length}`,
      `Best All-Time Score: ${this.bestScore}`
    ].filter(Boolean).join("\n");

    alert(summary);
  }

  getDailyBoardKey() {
    const seed = this.dailySeed || this.makeDailySeed();
    return `remix2048_daily_${seed}`;
  }

  getAllTimeBoardKey() {
    return "remix2048_all_time_board";
  }

  readBoard(key) {
    try {
      const raw = localStorage.getItem(key);
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }

  writeBoard(key, list) {
    localStorage.setItem(key, JSON.stringify(list.slice(0, 5)));
  }

  recordLeaderboardResult() {
    const nowIso = new Date().toISOString();
    const entry = {
      name: this.playerName,
      score: this.score,
      mode: this.modeName,
      size: this.size,
      steps: this.stepsTaken,
      dailySeed: this.dailySeed,
      at: nowIso,
      clientId: this.clientId
    };

    const allTime = this.readBoard(this.getAllTimeBoardKey());
    allTime.push(entry);
    allTime.sort((a, b) => b.score - a.score || a.steps - b.steps);
    this.writeBoard(this.getAllTimeBoardKey(), allTime);

    const dailyKey = this.getDailyBoardKey();
    const daily = this.readBoard(dailyKey);
    daily.push(entry);
    daily.sort((a, b) => b.score - a.score || a.steps - b.steps);
    this.writeBoard(dailyKey, daily);

    this.submitOnlineScore(entry);
  }

  mergeBoards(localRows, onlineRows) {
    const normalized = [];
    const pushRow = (row, source) => {
      const safe = {
        name: row.name || "Player",
        score: Number(row.score || 0),
        mode: row.mode || "Classic",
        size: Number(row.size || 4),
        steps: Number(row.steps || 0),
        source
      };
      normalized.push(safe);
    };

    localRows.forEach((row) => pushRow(row, "local"));
    onlineRows.forEach((row) => pushRow(row, "cloud"));

    normalized.sort((a, b) => b.score - a.score || a.steps - b.steps);
    return normalized.slice(0, 5);
  }

  async fetchCloudBoard(scope, seed = null) {
    const params = new URLSearchParams({ scope });
    if (seed) params.set("seed", String(seed));
    const response = await fetch(`${this.apiBase}/leaderboard?${params.toString()}`);
    if (!response.ok) throw new Error("cloud board fetch failed");
    const payload = await response.json();
    if (!payload || !Array.isArray(payload.entries)) return [];
    return payload.entries;
  }

  async submitOnlineScore(entry) {
    try {
      const response = await fetch(`${this.apiBase}/score`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(entry)
      });
      if (!response.ok) throw new Error("submit failed");
      this.cloudReachable = true;
      this.setCloudStatus("online", true);
    } catch {
      this.cloudReachable = false;
      this.setCloudStatus("offline fallback", false);
    }
  }

  async refreshOnlineLeaderboards(force = false) {
    const now = Date.now();
    if (!force && now - this.lastCloudFetchAt < 12000) return;
    this.lastCloudFetchAt = now;

    try {
      const seed = this.dailySeed || this.makeDailySeed();
      const [daily, all] = await Promise.all([
        this.fetchCloudBoard("daily", seed),
        this.fetchCloudBoard("all")
      ]);
      this.onlineDailyBoard = daily;
      this.onlineAllTimeBoard = all;
      this.cloudReachable = true;
      this.setCloudStatus("online", true);
      this.renderLeaderboard();
    } catch {
      this.cloudReachable = false;
      this.onlineDailyBoard = [];
      this.onlineAllTimeBoard = [];
      this.setCloudStatus("offline fallback", false);
      this.renderLeaderboard();
    }
  }

  renderLeaderboard() {
    const dailyLocal = this.readBoard(this.getDailyBoardKey());
    const allLocal = this.readBoard(this.getAllTimeBoardKey());
    const daily = this.mergeBoards(dailyLocal, this.onlineDailyBoard);
    const allTime = this.mergeBoards(allLocal, this.onlineAllTimeBoard);

    const fill = (target, rows) => {
      target.innerHTML = "";
      if (!rows.length) {
        const li = document.createElement("li");
        li.textContent = "No record yet";
        target.appendChild(li);
        return;
      }

      rows.slice(0, 5).forEach((row) => {
        const li = document.createElement("li");
        li.textContent = `${row.score} pts | ${row.name} | ${row.mode} ${row.size}x${row.size} | ${row.steps} steps | ${row.source}`;
        target.appendChild(li);
      });
    };

    fill(this.refs.dailyBoard, daily);
    fill(this.refs.allTimeBoard, allTime);
  }

  renderBoard() {
    for (let r = 0; r < this.size; r += 1) {
      for (let c = 0; c < this.size; c += 1) {
        const val = this.grid[r][c];
        const node = this.getCellNode(r, c);
        node.textContent = val === 0 ? "" : String(val);
        node.style.background = TILE_COLORS[val] || "#2b2520";
        node.style.color = val < 8 ? "#5f4f3a" : "#fff7ef";
        node.classList.toggle("frozen", this.isFrozen(r, c));
      }
    }
  }

  renderTasks() {
    this.refs.tasks.innerHTML = "";
    if (!this.tasks.length) {
      const li = document.createElement("li");
      li.className = "task-running";
      li.textContent = "No active tasks";
      this.refs.tasks.appendChild(li);
      return;
    }

    this.tasks.forEach((task, idx) => {
      const status = this.taskStatus(task);
      const li = document.createElement("li");
      li.className = `task-${status}`;
      li.textContent = `${idx + 1}. ${this.taskText(task)} [${status.toUpperCase()}]`;
      this.refs.tasks.appendChild(li);
    });
  }

  renderTools() {
    this.refs.hammerBtn.textContent = `Hammer (${this.hammerUses})`;
    this.refs.freezeBtn.textContent = `Freeze (${this.freezeUses})`;
    this.refs.pauseBtn.textContent = this.isPaused ? "Resume" : "Pause";
    this.refs.muteBtn.textContent = this.isMuted ? "Mute On" : "Mute Off";

    this.refs.hammerBtn.classList.toggle("active-tool", this.selectedTool === "hammer");
    this.refs.freezeBtn.classList.toggle("active-tool", this.selectedTool === "freeze");

    const canPlay = !this.gameOver && !this.isPaused;
    this.refs.hammerBtn.disabled = !(canPlay && this.hammerUses > 0);
    this.refs.freezeBtn.disabled = !(canPlay && this.freezeUses > 0);
    this.refs.undoBtn.disabled = !(canPlay && this.lastState);
    this.refs.pauseBtn.disabled = this.gameOver;

    this.refs.toolStatus.textContent =
      `Active: ${this.selectedTool || "None"} | Frozen: ${Object.keys(this.frozenCells).length} | Pause: ${this.isPaused ? "Yes" : "No"} | Mute: ${this.isMuted ? "On" : "Off"}`;
  }

  renderModeStatus() {
    if (this.modeName === "Timed") {
      this.refs.modeStatus.textContent = `Mode: Timed | Time Left: ${this.remainingTime}s`;
      return;
    }
    if (this.modeName === "Steps") {
      this.refs.modeStatus.textContent = `Mode: Steps | Remaining Moves: ${Math.max(0, this.stepsLimit - this.stepsTaken)}`;
      return;
    }
    if (this.modeName === "Daily") {
      this.refs.modeStatus.textContent = `Mode: Daily | Seed: ${this.dailySeed} | Fixed Grid: 4x4`;
      return;
    }
    this.refs.modeStatus.textContent = "Mode: Classic";
  }

  renderStats() {
    this.refs.score.textContent = String(this.score);
    this.refs.combo.textContent = `x${this.getComboMultiplier().toFixed(1)}`;
    this.refs.steps.textContent = String(this.stepsTaken);
    this.refs.best.textContent = String(this.bestScore);
  }

  renderAll() {
    this.renderStats();
    this.renderBoard();
    this.renderTasks();
    this.renderTools();
    this.renderModeStatus();
    this.renderLeaderboard();
    this.checkMilestones();

    if (!this.gameOver && this.checkGameOver()) this.endGame("No more valid moves");
  }

  animateMoveFeedback(previousGrid, nextGrid, spawnedPos) {
    const changed = [];
    for (let r = 0; r < this.size; r += 1) {
      for (let c = 0; c < this.size; c += 1) {
        if (previousGrid[r][c] !== nextGrid[r][c] && nextGrid[r][c] !== 0) changed.push([r, c]);
      }
    }
    if (spawnedPos) changed.push(spawnedPos);

    if (!changed.length) return;

    this.isAnimating = true;
    let i = 0;
    const pulse = () => {
      if (i >= changed.length) {
        this.isAnimating = false;
        this.renderBoard();
        return;
      }

      const [r, c] = changed[i];
      const node = this.getCellNode(r, c);
      node.style.boxShadow = `inset 0 0 0 3px ${spawnedPos && spawnedPos[0] === r && spawnedPos[1] === c ? "#1f7a8c" : "#d8613c"}`;

      setTimeout(() => {
        if (this.isFrozen(r, c)) {
          node.style.boxShadow = "inset 0 0 0 3px #2f8fb9";
        } else {
          node.style.boxShadow = "";
        }
        i += 1;
        pulse();
      }, 55);
    };

    pulse();
  }

  toast(message) {
    if (this.isMuted) return;
    this.refs.toast.textContent = message;
    this.refs.toast.classList.remove("hidden");
    clearTimeout(this.toastTimer);
    this.toastTimer = setTimeout(() => this.refs.toast.classList.add("hidden"), 1300);
  }
}

window.addEventListener("DOMContentLoaded", () => {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("./service-worker.js").catch(() => {
      // Silent fail for unsupported/private contexts.
    });
  }
  // eslint-disable-next-line no-new
  new Remix2048Web();
});
