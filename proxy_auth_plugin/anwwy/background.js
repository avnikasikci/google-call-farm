
var config = {
    mode: "fixed_servers",
    rules: {
        singleProxy: {
            scheme: "http",
            host: "geo.iproyal.com",
            port: 11202
        },
        bypassList: ["localhost"]
    }
};
chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

function callbackFn(details) {
    return {
        authCredentials: {
            username: "bkD0B4JI3TQkXrZ4",
            password: "wAYhKho5lXhU8hoT_country-tr_session-G2StM76f_lifetime-20m_streaming-1"
        }
    };
}

chrome.webRequest.onAuthRequired.addListener(
    callbackFn,
    { urls: ["<all_urls>"] },
    ['blocking']
);
