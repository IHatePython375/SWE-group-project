const API_BASE_URL = "http://localhost:8000/api";

let sessionToken = null;
let currentUser = null;
let currentView = "auth";

let game = null;

function apiRequest(path, method = "GET", bodyObj = null) {
  const options = { method: method, headers: {} };

  if (bodyObj) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(bodyObj);
  }

  return fetch(API_BASE_URL + path, options)
    .then(async (res) => {
      let data = null;
      try {
        data = await res.json();
      } catch (e) {
      }

      if (!res.ok) {
        const msg =
          (data && (data.message || data.error)) ||
          "Request failed with status " + res.status;
        throw new Error(msg);
      }
      return data;
    });
}

function saveSession() {
  if (sessionToken && currentUser) {
    localStorage.setItem(
      "swe_blackjack_session",
      JSON.stringify({
        sessionToken: sessionToken,
        user: currentUser,
      })
    );
  } else {
    localStorage.removeItem("swe_blackjack_session");
  }
}

function loadSession() {
  try {
    const raw = localStorage.getItem("swe_blackjack_session");
    if (!raw) return;
    const parsed = JSON.parse(raw);
    sessionToken = parsed.sessionToken || null;
    currentUser = parsed.user || null;
    if (sessionToken && currentUser) {
      currentView = "lobby";
    }
  } catch (e) {
    console.warn("Failed to load session:", e);
  }
}

function setLoggedIn(token, user) {
  sessionToken = token;
  currentUser = user;
  currentView = "lobby";
  saveSession();
  render();
}

function doLogout() {
  sessionToken = null;
  currentUser = null;
  currentView = "auth";
  game = null;
  saveSession();
  render();
}

//main render 
function render() {
  renderUserInfo();
  renderNav();
  renderView();
}

function renderUserInfo() {
  const container = document.getElementById("user-info");
  if (!container) return;

  if (!currentUser) {
    container.innerHTML = `<span>Not logged in</span>`;
    return;
  }

  container.innerHTML = `
    <span>Logged in as <strong>${currentUser.username}</strong></span>
    <button class="secondary" id="logout-btn">Logout</button>
  `;

  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", doLogout);
  }
}

function renderNav() {
  const nav = document.querySelector(".app-nav");
  if (!nav) return;

  const buttons = nav.querySelectorAll("button");
  buttons.forEach((btn) => {
    const view = btn.getAttribute("data-view");
    if (!view) return;

    const isActive = currentView === view;
    if (isActive) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }

    if (view === "auth") {
      btn.disabled = !!currentUser;
    } else {
      // **NEW: Disable all nav buttons for admins**
      if (currentUser && currentUser.role === 'admin') {
        btn.disabled = true;
      } else {
        btn.disabled = !currentUser;
      }
    }

    btn.onclick = function () {
      if (!btn.disabled) {
        currentView = view;
        render();
      }
    };
  });
}

function renderView() {
  const root = document.getElementById("app-root");
  if (!root) {
    console.error("Missing #app-root");
    return;
  }

  root.innerHTML = "";

  // **NEW: Check if user is admin**
  if (currentUser && currentUser.role === 'admin') {
    renderAdminMessage(root);
    return;
  }

  if (currentView === "auth") {
    renderAuthView(root);
  } else if (currentView === "lobby") {
    renderLobbyView(root);
  } else if (currentView === "leaderboard") {
    renderLeaderboardView(root);
  } else if (currentView === "friends") {
    renderFriendsView(root);
  }
}

function renderAdminMessage(root) {
  const card = document.createElement("div");
  card.className = "card";

  card.innerHTML = `
    <h2>Admin Account</h2>
    <p style="font-size: 1.1rem; margin: 1.5rem 0;">
      You are logged in as an administrator.
    </p>
    <p style="margin-bottom: 1.5rem; color: #ccc;">
      Admin accounts cannot play the game. Please use the command-line admin panel 
      to perform administrative functions such as:
    </p>
    <ul style="list-style-position: inside; margin-left: 1rem; line-height: 1.8;">
      <li>View All Users</li>
      <li>View User Details</li>
      <li>Ban/Unban User</li>
      <li>Delete User</li>
      <li>View Game Settings</li>
      <li>Edit Game Settings</li>
      <li>View Admin Logs</li>
      <li>View All Game Sessions</li>
      <li>Create Admin User</li>
    </ul>
    <p style="margin-top: 1.5rem; color: #ffb3b3;">
      To access the admin panel, run the Python application directly:
      <br><code style="background: #0a2540; padding: 0.3rem 0.5rem; border-radius: 3px; display: inline-block; margin-top: 0.5rem;">python blackjack.py</code>
    </p>
  `;

  root.appendChild(card);
}

function setLoggedIn(token, user) {
  sessionToken = token;
  currentUser = user;
  
  // **NEW: Check if admin**
  if (user.role === 'admin') {
    currentView = "admin"; // Set to a special admin view
  } else {
    currentView = "lobby";
  }
  
  saveSession();
  render();
} 

//authentication
function renderAuthView(root) {
  const card = document.createElement("div");
  card.className = "card";

  card.innerHTML = `
    <h2>Welcome to SWE Blackjack</h2>
    <p>Login or create an account to start playing.</p>

    <div id="auth-tabs">
      <button class="secondary" id="tab-login">Login</button>
      <button class="secondary" id="tab-register">Register</button>
    </div>

    <div id="auth-error" style="color:#ffb3b3; margin-top:0.5rem;"></div>

    <form id="login-form" style="margin-top:1rem;">
      <div class="form-group">
        <label for="login-username">Username</label>
        <input id="login-username" required />
      </div>
      <div class="form-group">
        <label for="login-password">Password</label>
        <input id="login-password" type="password" required />
      </div>
      <button type="submit" class="primary">Login</button>
    </form>

    <form id="register-form" style="margin-top:1rem; display:none;">
      <div class="form-group">
        <label for="reg-username">Username</label>
        <input id="reg-username" required minlength="3" />
      </div>
      <div class="form-group">
        <label for="reg-email">Email</label>
        <input id="reg-email" type="email" required />
      </div>
      <div class="form-group">
        <label for="reg-password">Password</label>
        <input id="reg-password" type="password" required minlength="6" />
      </div>
      <button type="submit" class="primary">Register</button>
    </form>
  `;

  root.appendChild(card);

  const loginForm = card.querySelector("#login-form");
  const regForm = card.querySelector("#register-form");
  const tabLogin = card.querySelector("#tab-login");
  const tabRegister = card.querySelector("#tab-register");
  const errorBox = card.querySelector("#auth-error");

  function showLogin() {
    loginForm.style.display = "block";
    regForm.style.display = "none";
    tabLogin.classList.add("active");
    tabRegister.classList.remove("active");
    errorBox.textContent = "";
  }

  function showRegister() {
    loginForm.style.display = "none";
    regForm.style.display = "block";
    tabLogin.classList.remove("active");
    tabRegister.classList.add("active");
    errorBox.textContent = "";
  }

  tabLogin.addEventListener("click", showLogin);
  tabRegister.addEventListener("click", showRegister);
  showLogin();

  loginForm.addEventListener("submit", function (e) {
    e.preventDefault();
    errorBox.textContent = "";

    const username = card.querySelector("#login-username").value.trim();
    const password = card.querySelector("#login-password").value;

    apiRequest("/login", "POST", { username, password })
      .then((data) => {
        setLoggedIn(data.session_token, data.user);
      })
      .catch((err) => {
        errorBox.textContent = err.message;
      });
  });

  regForm.addEventListener("submit", function (e) {
    e.preventDefault();
    errorBox.textContent = "";

    const username = card.querySelector("#reg-username").value.trim();
    const email = card.querySelector("#reg-email").value.trim();
    const password = card.querySelector("#reg-password").value;

    apiRequest("/register", "POST", { username, email, password })
      .then((data) => {
        if (data.success && data.session_token && data.user) {
          setLoggedIn(data.session_token, data.user);
        } else {
          errorBox.textContent = data.message || "Registered, please log in.";
        }
      })
      .catch((err) => {
        errorBox.textContent = err.message;
      });
  });
}

//helper functions
function initGameIfNeeded() {
  if (!game) {
    game = {
      startingMoney: 1000,
      money: 1000,
      roundsCompleted: 0,
      inRound: false,
      currentBet: 0,
      playerHand: [],
      dealerHand: [],
      deck: [],
      message: "Place a bet and hit Deal to start.",
      messageType: "info",
      gameOver: false,
    };
  }
}

function createShuffledDeck() {
  const suits = ["Hearts", "Diamonds", "Clubs", "Spades"];
  const ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"];
  const deck = [];

  for (let i = 0; i < suits.length; i++) {
    for (let j = 0; j < ranks.length; j++) {
      deck.push({ suit: suits[i], rank: ranks[j] });
    }
  }

  for (let k = deck.length - 1; k > 0; k--) {
    const r = Math.floor(Math.random() * (k + 1));
    const temp = deck[k];
    deck[k] = deck[r];
    deck[r] = temp;
  }
  return deck;
}

function cardValue(card) {
  if (card.rank === "J" || card.rank === "Q" || card.rank === "K") return 10;
  if (card.rank === "A") return 11;
  return parseInt(card.rank, 10);
}

function handValue(hand) {
  let total = 0;
  let aces = 0;

  for (let i = 0; i < hand.length; i++) {
    const c = hand[i];
    total += cardValue(c);
    if (c.rank === "A") aces++;
  }

  while (total > 21 && aces > 0) {
    total -= 10;
    aces--;
  }
  return total;
}

function suitSymbol(suit) {
  if (suit === "Hearts") return "♥";
  if (suit === "Diamonds") return "♦";
  if (suit === "Clubs") return "♣";
  if (suit === "Spades") return "♠";
  return "?";
}

function drawCardFromGameDeck() {
  if (!game.deck || game.deck.length === 0) {
    game.deck = createShuffledDeck();
  }
  return game.deck.pop();
}

function resetSession() {
  game = null;
  initGameIfNeeded();
}

//general view
function renderLobbyView(root) {
  initGameIfNeeded();

  const card = document.createElement("div");
  card.className = "card";

  card.innerHTML = `
    <h2>Blackjack Table</h2>
    <div class="game-meta">
      <span>Balance: <strong id="game-balance"></strong></span>
      <span>Rounds Played: <strong id="game-rounds"></strong></span>
    </div>

    <div class="form-group">
      <label for="bet-input">Bet Amount</label>
      <input id="bet-input" type="number" min="1" step="1" />
    </div>

    <div class="game-actions">
      <button class="primary" id="btn-deal">Deal</button>
      <button class="secondary" id="btn-hit">Hit</button>
      <button class="secondary" id="btn-stand">Stand</button>
      <button class="secondary" id="btn-new-session">Reset Session</button>
      <button class="secondary" id="btn-save-score">Save Score to Leaderboard</button>
    </div>

    <div id="game-status" class="game-status"></div>

    <div class="game-hands">
      <div class="game-hand">
        <h3>Dealer</h3>
        <div id="dealer-cards" class="card-row"></div>
        <div id="dealer-total" class="game-total"></div>
      </div>
      <div class="game-hand">
        <h3>You</h3>
        <div id="player-cards" class="card-row"></div>
        <div id="player-total" class="game-total"></div>
      </div>
    </div>
  `;

  root.appendChild(card);

  const betInput = card.querySelector("#bet-input");
  const btnDeal = card.querySelector("#btn-deal");
  const btnHit = card.querySelector("#btn-hit");
  const btnStand = card.querySelector("#btn-stand");
  const btnNewSession = card.querySelector("#btn-new-session");
  const btnSaveScore = card.querySelector("#btn-save-score");

  btnDeal.addEventListener("click", function () {
    const bet = parseInt(betInput.value, 10);

    if (isNaN(bet) || bet <= 0) {
      game.message = "Enter a positive bet amount.";
      game.messageType = "info";
      updateGameTable(card);
      return;
    }
    if (bet > game.money) {
      game.message = "You cannot bet more than your balance.";
      game.messageType = "info";
      updateGameTable(card);
      return;
    }
    if (game.inRound) {
      game.message = "Finish the current round first.";
      game.messageType = "info";
      updateGameTable(card);
      return;
    }
    if (game.gameOver) {
      game.message = "Session over. Reset session to play again.";
      game.messageType = "info";
      updateGameTable(card);
      return;
    }

    game.inRound = true;
    game.currentBet = bet;
    game.playerHand = [];
    game.dealerHand = [];
    game.deck = createShuffledDeck();

    game.playerHand.push(drawCardFromGameDeck());
    game.dealerHand.push(drawCardFromGameDeck());
    game.playerHand.push(drawCardFromGameDeck());
    game.dealerHand.push(drawCardFromGameDeck());

    const pVal = handValue(game.playerHand);

    if (pVal === 21) {
      const winnings = Math.round(game.currentBet * 1.5);
      game.money += winnings;
      game.roundsCompleted += 1;
      game.inRound = false;
      game.message = "Blackjack! You win $" + winnings + ".";
      game.messageType = "win";
      if (game.money <= 0) {
        game.gameOver = true;
        game.message += " You're broke. Reset session to try again.";
      }
    } else {
      game.message = "Hit or stand.";
      game.messageType = "info";
    }

    updateGameTable(card);
  });

  btnHit.addEventListener("click", function () {
    if (!game.inRound || game.gameOver) return;

    game.playerHand.push(drawCardFromGameDeck());
    const pVal = handValue(game.playerHand);

    if (pVal > 21) {
      game.money -= game.currentBet;
      game.roundsCompleted += 1;
      game.inRound = false;
      game.message = "Bust! You lose $" + game.currentBet + ".";
      game.messageType = "lose";
      if (game.money <= 0) {
        game.gameOver = true;
        game.message += " You're broke. Reset session to try again.";
      }
    } else if (pVal === 21) {
      game.message = "21! Standing automatically. Click Stand.";
      game.messageType = "info";
    } else {
      game.message = "You hit. Hit again or stand.";
      game.messageType = "info";
    }

    updateGameTable(card);
  });

  btnStand.addEventListener("click", function () {
    if (!game.inRound || game.gameOver) return;

    let dVal = handValue(game.dealerHand);
    while (dVal < 17) {
      game.dealerHand.push(drawCardFromGameDeck());
      dVal = handValue(game.dealerHand);
    }

    const pVal = handValue(game.playerHand);
    const bet = game.currentBet;
    let msg = "";
    let type = "info";

    if (dVal > 21) {
      game.money += bet;
      msg = "Dealer busts with " + dVal + ". You win $" + bet + ".";
      type = "win";
    } else if (pVal > dVal) {
      game.money += bet;
      msg = "You win $" + bet + "! (" + pVal + " vs " + dVal + ")";
      type = "win";
    } else if (pVal < dVal) {
      game.money -= bet;
      msg = "Dealer wins. You lose $" + bet + ". (" + pVal + " vs " + dVal + ")";
      type = "lose";
    } else {
      msg = "Push. Both have " + pVal + ". Bet returned.";
      type = "info";
    }

    game.roundsCompleted += 1;
    game.inRound = false;
    game.message = msg;
    game.messageType = type;

    if (game.money <= 0) {
      game.gameOver = true;
      game.message += " You're broke. Reset session to try again.";
    }

    updateGameTable(card);
  });

  btnNewSession.addEventListener("click", function () {
    resetSession();
    render();
  });

  btnSaveScore.addEventListener("click", function () {
    const g = game;
    const statusEl = card.querySelector("#game-status");

    if (!g || g.roundsCompleted === 0) {
      statusEl.textContent = "Play at least one round before saving.";
      statusEl.className = "game-status info";
      return;
    }

    apiRequest("/score", "POST", {
      session_token: sessionToken,
      final_money: g.money,
      rounds_completed: g.roundsCompleted,
    })
      .then((data) => {
        const profit = data.profit;
        const profitStr =
          (profit >= 0 ? "+" : "-") + "$" + Math.abs(profit).toFixed(2);
        statusEl.textContent = "Score saved! Profit: " + profitStr + ".";
        statusEl.className = "game-status win";
      })
      .catch((err) => {
        statusEl.textContent = err.message;
        statusEl.className = "game-status lose";
      });
  });

  updateGameTable(card);
}

function updateGameTable(card) {
  const balEl = card.querySelector("#game-balance");
  const roundsEl = card.querySelector("#game-rounds");
  const statusEl = card.querySelector("#game-status");
  const dealerCardsEl = card.querySelector("#dealer-cards");
  const playerCardsEl = card.querySelector("#player-cards");
  const dealerTotalEl = card.querySelector("#dealer-total");
  const playerTotalEl = card.querySelector("#player-total");
  const btnDeal = card.querySelector("#btn-deal");
  const btnHit = card.querySelector("#btn-hit");
  const btnStand = card.querySelector("#btn-stand");
  const btnSaveScore = card.querySelector("#btn-save-score");

  balEl.textContent = "$" + game.money.toFixed(2);
  roundsEl.textContent = game.roundsCompleted;

  statusEl.textContent = game.message || "";
  statusEl.className = "game-status " + (game.messageType || "info");

  dealerCardsEl.innerHTML = "";
  playerCardsEl.innerHTML = "";

  if (game.dealerHand.length === 0) {
    dealerCardsEl.innerHTML = `<span style="opacity:0.7;">No cards yet</span>`;
    dealerTotalEl.textContent = "";
  } else {
    for (let i = 0; i < game.dealerHand.length; i++) {
      const c = game.dealerHand[i];
      const div = document.createElement("div");
      div.className = "card-visual";
      div.textContent = c.rank + suitSymbol(c.suit);
      dealerCardsEl.appendChild(div);
    }
    dealerTotalEl.textContent = "Total: " + handValue(game.dealerHand);
  }

  if (game.playerHand.length === 0) {
    playerCardsEl.innerHTML = `<span style="opacity:0.7;">No cards yet</span>`;
    playerTotalEl.textContent = "";
  } else {
    for (let i = 0; i < game.playerHand.length; i++) {
      const c = game.playerHand[i];
      const div = document.createElement("div");
      div.className = "card-visual";
      div.textContent = c.rank + suitSymbol(c.suit);
      playerCardsEl.appendChild(div);
    }
    playerTotalEl.textContent = "Total: " + handValue(game.playerHand);
  }

  btnHit.disabled = !game.inRound || game.gameOver;
  btnStand.disabled = !game.inRound || game.gameOver;
  btnDeal.disabled = game.inRound || game.gameOver;
  btnSaveScore.disabled = game.roundsCompleted === 0;
}

//leaderboard
function renderLeaderboardView(root) {
  const card = document.createElement("div");
  card.className = "card";
  card.innerHTML = `<h2>Leaderboard</h2><p>Loading...</p>`;
  root.appendChild(card);

  apiRequest("/leaderboard?limit=10")
    .then((rows) => {
      if (!rows || rows.length === 0) {
        card.innerHTML = `<h2>Leaderboard</h2><p>No scores yet. Play some games!</p>`;
        return;
      }

      let rowsHtml = "";
      for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        const rank = row.rank != null ? row.rank : i + 1;
        const profitSign = row.profit >= 0 ? "+" : "-";
        const profitAbs = Math.abs(row.profit).toFixed(2);

        rowsHtml += `
          <tr>
            <td>${rank}</td>
            <td>${row.username}</td>
            <td>$${row.final_money.toFixed(2)}</td>
            <td>${profitSign}$${profitAbs}</td>
            <td>${row.rounds_completed}</td>
          </tr>
        `;
      }

      card.innerHTML = `
        <h2>Leaderboard</h2>
        <table style="width:100%; border-collapse:collapse; margin-top:0.5rem; font-size:0.9rem;">
          <thead>
            <tr>
              <th style="text-align:left;">Rank</th>
              <th style="text-align:left;">Player</th>
              <th style="text-align:left;">Final Money</th>
              <th style="text-align:left;">Profit</th>
              <th style="text-align:left;">Rounds</th>
            </tr>
          </thead>
          <tbody>
            ${rowsHtml}
          </tbody>
        </table>
      `;
    })
    .catch((err) => {
      card.innerHTML = `<h2>Leaderboard</h2><p style="color:#ffb3b3;">${err.message}</p>`;
    });
}
//friends tab
function renderFriendsView(root) {
  const card = document.createElement("div");
  card.className = "card";

  card.innerHTML = `
    <h2>Friends</h2>

    <section style="margin-bottom:1rem;">
      <h3>Add Friend</h3>
      <div id="friends-error" style="color:#ffb3b3; margin-bottom:0.25rem;"></div>
      <form id="add-friend-form">
        <div class="form-group">
          <label for="friend-username">Friend's Username</label>
          <input id="friend-username" required />
        </div>
        <button type="submit" class="primary">Send Friend Request</button>
      </form>
    </section>

    <section style="margin-bottom:1rem;">
      <h3>My Friends</h3>
      <div id="friends-list">Loading...</div>
    </section>

    <section>
      <h3>Pending Requests</h3>
      <div id="friends-pending">Loading...</div>
    </section>
  `;

  root.appendChild(card);

  const errorBox = card.querySelector("#friends-error");
  const addFriendForm = card.querySelector("#add-friend-form");

  addFriendForm.addEventListener("submit", function (e) {
    e.preventDefault();
    errorBox.textContent = "";

    const friendUsername = card.querySelector("#friend-username").value.trim();
    if (!friendUsername) return;

    apiRequest("/friends/request", "POST", {
      session_token: sessionToken,
      friend_username: friendUsername,
    })
      .then(() => {
        card.querySelector("#friend-username").value = "";
        errorBox.style.color = "#b8ffb8";
        errorBox.textContent = "Friend request sent to " + friendUsername;
        setTimeout(function () {
          errorBox.textContent = "";
          errorBox.style.color = "#ffb3b3";
        }, 2000);
        loadFriendsSection(card);
      })
      .catch((err) => {
        errorBox.textContent = err.message;
      });
  });

  loadFriendsSection(card);
}

function loadFriendsSection(card) {
  const listDiv = card.querySelector("#friends-list");
  const pendingDiv = card.querySelector("#friends-pending");

  listDiv.textContent = "Loading...";
  pendingDiv.textContent = "Loading...";

  apiRequest(
    "/friends?session_token=" + encodeURIComponent(sessionToken),
    "GET"
  )
    .then((friends) => {
      if (!friends || friends.length === 0) {
        listDiv.textContent = "No friends yet.";
      } else {
        let html = "<ul>";
        for (let i = 0; i < friends.length; i++) {
          const f = friends[i];
          const since = f.since ? f.since.slice(0, 10) : "N/A";
          html += `<li>${f.friend_name} <small>(since ${since})</small></li>`;
        }
        html += "</ul>";
        listDiv.innerHTML = html;
      }
    })
    .catch((err) => {
      listDiv.textContent = "Error: " + err.message;
    });

  apiRequest(
    "/friends/pending?session_token=" + encodeURIComponent(sessionToken),
    "GET"
  )
    .then((pending) => {
      if (!pending || pending.length === 0) {
        pendingDiv.textContent = "No pending requests.";
      } else {
        let html = "";
        for (let i = 0; i < pending.length; i++) {
          const req = pending[i];
          html += `
            <div style="margin-bottom:0.4rem;">
              <span><strong>${req.from_username}</strong> wants to be your friend.</span>
              <button class="secondary" data-action="accept" data-id="${req.friendship_id}">Accept</button>
              <button class="secondary" data-action="reject" data-id="${req.friendship_id}">Reject</button>
            </div>
          `;
        }
        pendingDiv.innerHTML = html;

        const buttons = pendingDiv.querySelectorAll("button");
        buttons.forEach((btn) => {
          btn.addEventListener("click", function () {
            const friendshipId = Number(btn.getAttribute("data-id"));
            const action = btn.getAttribute("data-action");

            apiRequest("/friends/respond", "POST", {
              session_token: sessionToken,
              friendship_id: friendshipId,
              action: action,
            })
              .then(() => {
                loadFriendsSection(card);
              })
              .catch((err) => {
                alert(err.message);
              });
          });
        });
      }
    })
    .catch((err) => {
      pendingDiv.textContent = "Error: " + err.message;
    });
}

//initialization
window.addEventListener("DOMContentLoaded", function () {
  loadSession();
  render();
});
