var API_BASE_URL = "http://127.0.0.1:8000";

function apiPost(path, data) {
    return fetch(API_BASE_URL + path, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    }).then(function (response) {
        if (!response.ok) {
            return response.json().catch(function () {
                throw new Error("Request failed with status " + response.status);
            }).then(function (data) {
                if (data && data.message) {
                    throw new Error(data.message);
                } else if (data && data.error) {
                    throw new Error(data.error);
                } else {
                    throw new Error("Request failed with status " + response.status);
                }
            });
        }
        return response.json();
    });
}

function apiGet(path, params) {
    var url = API_BASE_URL + path;
    if (params) {
        var query = new URLSearchParams(params).toString();
        url += "?" + query;
    }
    return fetch(url).then(function (response) {
        if (!response.ok) {
            throw new Error("Request failed with status " + response.status);
        }
        return response.json();
    });
}
