
// simple global state

let sessionToken = null;
let currentUser = null;

let currentMoney = 1000;
let roundsPlayed = 0;

const VIEWS = ["view-auth", "view-lobby", "view-leaderboard", "view-friends"];

// helper functions

function $(id) {
    return document.getElementById(id);
}

function showView(id) {
    VIEWS.forEach(viewId => {
        const el = $(viewId);
        if (!el) return;
        if (viewId === id) {
            el.classList.remove("hidden");
        } else {
            el.classList.add("hidden");
        }
    });
}

function setLoggedInUI(isLoggedIn) {
    const userStatus = $("user-status");
    const logoutBtn = $("logout-btn");
    const lobbyBtn = $("nav-lobby-btn");
    const leaderboardBtn = $("nav-leaderboard-btn");
    const friendsBtn = $("nav-friends-btn");

    if (isLoggedIn) {
        userStatus.textContent = "Logged in as " + currentUser.username;
        logoutBtn.classList.remove("hidden");

        lobbyBtn.disabled = false;
        leaderboardBtn.disabled = false;
        friendsBtn.disabled = false;
    } else {
        userStatus.textContent = "Not logged in";
        logoutBtn.classList.add("hidden");

        lobbyBtn.disabled = true;
        leaderboardBtn.disabled = true;
        friendsBtn.disabled = true;
    }
}

function updateGameDisplay() {
    const moneySpan = $("money-display");
    const roundsSpan = $("rounds-display");
    if (moneySpan) moneySpan.textContent = currentMoney.toFixed(2);
    if (roundsSpan) roundsSpan.textContent = roundsPlayed;
}


// the authentication handlers


function handleLogin() {
    const username = $("login-username").value.trim();
    const password = $("login-password").value;
    const msg = $("login-message");
    msg.textContent = "";

    if (!username || !password) {
        msg.textContent = "Please enter username and password.";
        return;
    }

    apiPost("/api/login", {
        username: username,
        password: password
    })
        .then(data => {
            sessionToken = data.session_token;
            currentUser = data.user;
            localStorage.setItem("sessionToken", sessionToken);
            localStorage.setItem("currentUser", JSON.stringify(currentUser));

            setLoggedInUI(true);
            msg.textContent = "";
            showView("view-lobby");
        })
        .catch(err => {
            msg.textContent = err.message || "Login failed.";
        });
}

function handleRegister() {
    const username = $("register-username").value.trim();
    const email = $("register-email").value.trim();
    const password = $("register-password").value;
    const msg = $("register-message");
    msg.textContent = "";

    if (!username || !email || !password) {
        msg.textContent = "Please fill out all fields.";
        return;
    }

    apiPost("/api/register", {
        username: username,
        email: email,
        password: password
    })
        .then(data => {
            if (data.session_token && data.user) {
                sessionToken = data.session_token;
                currentUser = data.user;
                localStorage.setItem("sessionToken", sessionToken);
                localStorage.setItem("currentUser", JSON.stringify(currentUser));

                setLoggedInUI(true);
                msg.textContent = "Registered and logged in.";
                showView("view-lobby");
            } else {
                msg.textContent = data.message || "Registered. Please login.";
            }
        })
        .catch(err => {
            msg.textContent = err.message || "Registration failed.";
        });
}

function handleLogout() {
    sessionToken = null;
    currentUser = null;
    localStorage.removeItem("sessionToken");
    localStorage.removeItem("currentUser");
    setLoggedInUI(false);
    showView("view-auth");
}


// tabs inside the auth card

function setupAuthTabs() {
    const tabLogin = $("tab-login");
    const tabRegister = $("tab-register");
    const loginForm = $("login-form");
    const registerForm = $("register-form");

    if (!tabLogin || !tabRegister) return;

    tabLogin.addEventListener("click", () => {
        tabLogin.classList.add("active");
        tabRegister.classList.remove("active");
        loginForm.classList.remove("hidden");
        registerForm.classList.add("hidden");
    });

    tabRegister.addEventListener("click", () => {
        tabRegister.classList.add("active");
        tabLogin.classList.remove("active");
        registerForm.classList.remove("hidden");
        loginForm.classList.add("hidden");
    });
}


// dealing

function handleDealHand() {
    const betInput = $("bet-input");
    const msg = $("round-result");
    msg.textContent = "";

    const bet = parseInt(betInput.value, 10);
    if (isNaN(bet) || bet <= 0) {
        msg.textContent = "Bet must be a positive number.";
        return;
    }
    if (bet > currentMoney) {
        msg.textContent = "You cannot bet more than you have.";
        return;
    }

    const r = Math.random();
    if (r < 0.45) {
        currentMoney += bet;
        msg.textContent = "You won $" + bet + "!";
    } else if (r < 0.90) {
        currentMoney -= bet;
        msg.textContent = "You lost $" + bet + ".";
    } else {
        msg.textContent = "Push. Your bet is returned.";
    }

    roundsPlayed += 1;
    updateGameDisplay();
}

function handleSaveScore() {
    const msg = $("save-score-message");
    msg.textContent = "";

    if (!sessionToken) {
        msg.textContent = "You must be logged in to save a score.";
        return;
    }

    apiPost("/api/score", {
        session_token: sessionToken,
        final_money: currentMoney,
        rounds_completed: roundsPlayed
    })
        .then(data => {
            msg.textContent = "Score saved! Leaderboard ID: " + data.leaderboard_id;
        })
        .catch(err => {
            msg.textContent = err.message || "Failed to save score.";
        });
}


// leaderboard

function loadLeaderboard() {
    const body = $("leaderboard-body");
    const msg = $("leaderboard-message");
    if (!body) return;
    body.innerHTML = "";
    msg.textContent = "";

    apiGet("/api/leaderboard", { limit: 10 })
        .then(rows => {
            if (!rows || rows.length === 0) {
                msg.textContent = "No scores yet.";
                return;
            }

            rows.forEach(row => {
                const tr = document.createElement("tr");

                const rankTd = document.createElement("td");
                rankTd.textContent = row.rank;
                tr.appendChild(rankTd);

                const nameTd = document.createElement("td");
                nameTd.textContent = row.username;
                tr.appendChild(nameTd);

                const moneyTd = document.createElement("td");
                moneyTd.textContent = "$" + row.final_money.toFixed(2);
                tr.appendChild(moneyTd);

                const profitTd = document.createElement("td");
                profitTd.textContent = "$" + row.profit.toFixed(2);
                tr.appendChild(profitTd);

                const roundsTd = document.createElement("td");
                roundsTd.textContent = row.rounds_completed;
                tr.appendChild(roundsTd);

                body.appendChild(tr);
            });
        })
        .catch(err => {
            msg.textContent = err.message || "Failed to load leaderboard.";
        });
}


// friends

function loadFriends() {
    const list = $("friends-list");
    const msg = $("friends-message");
    if (!list) return;
    list.innerHTML = "";
    msg.textContent = "";

    if (!sessionToken) {
        msg.textContent = "You must be logged in.";
        return;
    }

    apiGet("/api/friends", { session_token: sessionToken })
        .then(rows => {
            if (!rows || rows.length === 0) {
                list.innerHTML = "<li>No friends yet.</li>";
                return;
            }
            rows.forEach(friend => {
                const li = document.createElement("li");
                li.textContent = friend.friend_name;
                list.appendChild(li);
            });
        })
        .catch(err => {
            msg.textContent = err.message || "Failed to load friends.";
        });
}

function handleSendFriendRequest() {
    const input = $("friend-username-input");
    const msg = $("friends-message");
    msg.textContent = "";

    if (!sessionToken) {
        msg.textContent = "You must be logged in.";
        return;
    }

    const friendUsername = input.value.trim();
    if (!friendUsername) {
        msg.textContent = "Please enter a username.";
        return;
    }

    apiPost("/api/friends/request", {
        session_token: sessionToken,
        friend_username: friendUsername
    })
        .then(data => {
            msg.textContent = "Friend request sent to " + data.to_user + ".";
            input.value = "";
        })
        .catch(err => {
            msg.textContent = err.message || "Failed to send friend request.";
        });
}


// navigation

function setupNav() {
    const navAuth = $("nav-auth-btn");
    const navLobby = $("nav-lobby-btn");
    const navLeaderboard = $("nav-leaderboard-btn");
    const navFriends = $("nav-friends-btn");
    const logoutBtn = $("logout-btn");

    if (navAuth) {
        navAuth.addEventListener("click", () => showView("view-auth"));
    }
    if (navLobby) {
        navLobby.addEventListener("click", () => showView("view-lobby"));
    }
    if (navLeaderboard) {
        navLeaderboard.addEventListener("click", () => {
            showView("view-leaderboard");
            loadLeaderboard();
        });
    }
    if (navFriends) {
        navFriends.addEventListener("click", () => {
            showView("view-friends");
            loadFriends();
        });
    }
    if (logoutBtn) {
        logoutBtn.addEventListener("click", handleLogout);
    }
}

function setupButtons() {
    const loginBtn = $("login-submit");
    const registerBtn = $("register-submit");
    const dealBtn = $("deal-btn");
    const saveScoreBtn = $("save-score-btn");
    const refreshLeaderboardBtn = $("refresh-leaderboard-btn");
    const sendFriendRequestBtn = $("send-friend-request-btn");

    if (loginBtn) loginBtn.addEventListener("click", handleLogin);
    if (registerBtn) registerBtn.addEventListener("click", handleRegister);
    if (dealBtn) dealBtn.addEventListener("click", handleDealHand);
    if (saveScoreBtn) saveScoreBtn.addEventListener("click", handleSaveScore);
    if (refreshLeaderboardBtn) refreshLeaderboardBtn.addEventListener("click", loadLeaderboard);
    if (sendFriendRequestBtn) sendFriendRequestBtn.addEventListener("click", handleSendFriendRequest);
}

function restoreSession() {
    const token = localStorage.getItem("sessionToken");
    const userJson = localStorage.getItem("currentUser");

    if (token && userJson) {
        try {
            const userObj = JSON.parse(userJson);
            sessionToken = token;
            currentUser = userObj;
        } catch (e) {
            sessionToken = null;
            currentUser = null;
        }
    }

    if (sessionToken && currentUser) {
        setLoggedInUI(true);
        showView("view-lobby");
    } else {
        setLoggedInUI(false);
        showView("view-auth");
    }

    updateGameDisplay();
}

window.addEventListener("DOMContentLoaded", () => {
    setupAuthTabs();
    setupNav();
    setupButtons();
    restoreSession();
});
