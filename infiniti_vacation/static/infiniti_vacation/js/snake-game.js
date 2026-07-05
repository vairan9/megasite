(() => {
  const root = document.querySelector("[data-snake-game]");
  if (!root) return;

  const canvas = root.querySelector("[data-snake-canvas]");
  const context = canvas.getContext("2d");
  const scoreElement = root.querySelector("[data-snake-score]");
  const bestElement = root.querySelector("[data-snake-best]");
  const overlay = root.querySelector("[data-snake-overlay]");
  const message = root.querySelector("[data-snake-message]");
  const startButton = root.querySelector("[data-snake-start]");
  const startLabel = root.querySelector("[data-snake-start-label]");
  const pauseButton = root.querySelector("[data-snake-pause]");
  const resetButton = root.querySelector("[data-snake-reset]");
  const directionButtons = root.querySelectorAll("[data-snake-direction]");

  const gridSize = 20;
  const tileSize = canvas.width / gridSize;
  const initialSpeed = 125;
  const directionMap = {
    ArrowUp: { x: 0, y: -1 },
    ArrowDown: { x: 0, y: 1 },
    ArrowLeft: { x: -1, y: 0 },
    ArrowRight: { x: 1, y: 0 },
    w: { x: 0, y: -1 },
    s: { x: 0, y: 1 },
    a: { x: -1, y: 0 },
    d: { x: 1, y: 0 },
  };

  let snake;
  let food;
  let direction;
  let queuedDirection;
  let score;
  let speed;
  let timer = null;
  let state = "idle";
  let touchStart = null;

  function readBest() {
    try {
      return Number(localStorage.getItem("infiniti-snake-best")) || 0;
    } catch {
      return 0;
    }
  }

  function writeBest(value) {
    try {
      localStorage.setItem("infiniti-snake-best", String(value));
    } catch {
      // The game still works when browser storage is unavailable.
    }
  }

  let best = readBest();

  function randomFood() {
    let next;
    do {
      next = {
        x: Math.floor(Math.random() * gridSize),
        y: Math.floor(Math.random() * gridSize),
      };
    } while (snake.some(part => part.x === next.x && part.y === next.y));
    return next;
  }

  function resetGame() {
    stopTimer();
    snake = [
      { x: 10, y: 10 },
      { x: 9, y: 10 },
      { x: 8, y: 10 },
    ];
    direction = { x: 1, y: 0 };
    queuedDirection = { ...direction };
    score = 0;
    speed = initialSpeed;
    food = randomFood();
    state = "idle";
    updateScore();
    setOverlay("Gotowy?");
    startLabel.textContent = "Graj";
    startButton.disabled = false;
    pauseButton.disabled = true;
    draw();
  }

  function updateScore() {
    scoreElement.textContent = String(score);
    bestElement.textContent = String(best);
  }

  function setOverlay(text) {
    message.textContent = text;
    overlay.hidden = false;
  }

  function hideOverlay() {
    overlay.hidden = true;
  }

  function stopTimer() {
    if (timer) window.clearInterval(timer);
    timer = null;
  }

  function startTimer() {
    stopTimer();
    timer = window.setInterval(step, speed);
  }

  function startGame() {
    if (state === "over") resetGame();
    state = "running";
    hideOverlay();
    startLabel.textContent = "Wznow";
    startButton.disabled = true;
    pauseButton.disabled = false;
    startTimer();
    canvas.focus({ preventScroll: true });
  }

  function pauseGame() {
    if (state !== "running") return;
    state = "paused";
    stopTimer();
    startButton.disabled = false;
    startLabel.textContent = "Wznow";
    pauseButton.disabled = true;
    setOverlay("Pauza");
  }

  function gameOver() {
    state = "over";
    stopTimer();
    startButton.disabled = false;
    pauseButton.disabled = true;
    startLabel.textContent = "Jeszcze raz";
    setOverlay(`Koniec gry - ${score}`);
  }

  function setDirection(next) {
    if (!next) return;
    const isOpposite = next.x + direction.x === 0 && next.y + direction.y === 0;
    if (!isOpposite) queuedDirection = next;
  }

  function step() {
    direction = queuedDirection;
    const head = {
      x: snake[0].x + direction.x,
      y: snake[0].y + direction.y,
    };

    const willEat = head.x === food.x && head.y === food.y;
    const bodyToCheck = willEat ? snake : snake.slice(0, -1);
    const hitWall = head.x < 0 || head.x >= gridSize || head.y < 0 || head.y >= gridSize;
    const hitSnake = bodyToCheck.some(part => part.x === head.x && part.y === head.y);
    if (hitWall || hitSnake) {
      gameOver();
      return;
    }

    snake.unshift(head);
    if (willEat) {
      score += 1;
      if (score > best) {
        best = score;
        writeBest(best);
      }
      food = randomFood();
      updateScore();

      const nextSpeed = Math.max(65, initialSpeed - Math.floor(score / 4) * 8);
      if (nextSpeed !== speed) {
        speed = nextSpeed;
        startTimer();
      }
    } else {
      snake.pop();
    }

    draw();
  }

  function drawGrid() {
    context.strokeStyle = "rgba(255,255,255,.035)";
    context.lineWidth = 1;
    for (let i = 1; i < gridSize; i += 1) {
      const position = i * tileSize + .5;
      context.beginPath();
      context.moveTo(position, 0);
      context.lineTo(position, canvas.height);
      context.stroke();
      context.beginPath();
      context.moveTo(0, position);
      context.lineTo(canvas.width, position);
      context.stroke();
    }
  }

  function drawRoundedTile(x, y, inset, radius, color) {
    const left = x * tileSize + inset;
    const top = y * tileSize + inset;
    const size = tileSize - inset * 2;
    context.fillStyle = color;
    context.beginPath();
    context.roundRect(left, top, size, size, radius);
    context.fill();
  }

  function draw() {
    context.fillStyle = "#041009";
    context.fillRect(0, 0, canvas.width, canvas.height);
    drawGrid();

    context.fillStyle = "#7dd3fc";
    context.beginPath();
    context.arc(
      food.x * tileSize + tileSize / 2,
      food.y * tileSize + tileSize / 2,
      tileSize * .31,
      0,
      Math.PI * 2,
    );
    context.fill();

    snake.forEach((part, index) => {
      drawRoundedTile(
        part.x,
        part.y,
        1.8,
        index === 0 ? 6 : 5,
        index === 0 ? "#86efac" : "#4ade80",
      );
    });
  }

  startButton.addEventListener("click", startGame);
  pauseButton.addEventListener("click", pauseGame);
  resetButton.addEventListener("click", resetGame);

  directionButtons.forEach(button => {
    button.addEventListener("click", () => {
      const key = `Arrow${button.dataset.snakeDirection[0].toUpperCase()}${button.dataset.snakeDirection.slice(1)}`;
      setDirection(directionMap[key]);
      if (state === "idle" || state === "paused") startGame();
    });
  });

  document.addEventListener("keydown", event => {
    const key = event.key.length === 1 ? event.key.toLowerCase() : event.key;
    const next = directionMap[key];
    if (!next || (state !== "running" && document.activeElement !== canvas)) return;
    event.preventDefault();
    setDirection(next);
    if (state !== "running") startGame();
  });

  canvas.addEventListener("touchstart", event => {
    const touch = event.changedTouches[0];
    touchStart = { x: touch.clientX, y: touch.clientY };
  }, { passive: true });

  canvas.addEventListener("touchend", event => {
    if (!touchStart) return;
    const touch = event.changedTouches[0];
    const dx = touch.clientX - touchStart.x;
    const dy = touch.clientY - touchStart.y;
    touchStart = null;
    if (Math.max(Math.abs(dx), Math.abs(dy)) < 24) return;

    const next = Math.abs(dx) > Math.abs(dy)
      ? (dx > 0 ? directionMap.ArrowRight : directionMap.ArrowLeft)
      : (dy > 0 ? directionMap.ArrowDown : directionMap.ArrowUp);
    setDirection(next);
    if (state === "idle" || state === "paused") startGame();
  }, { passive: true });

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) pauseGame();
  });

  resetGame();
})();
