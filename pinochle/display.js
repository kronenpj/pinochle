var host = window.location.host;
var ws = new ReconnectingWebSocket('ws://' + host + '/ws');
var ws_connected = false;
ws.onopen = function () {
    $("body").attr("class", '');
    ws_connected = true;
    // console.log("Opened web socket.");
}
ws.onmessage = function (ev) {
    // console.log("Web socket received message.");
    // console.log(ev.data)
    if (ev.data === "{hand: true}") {
        // console.log("Updating hand.")
        updateHand();
    }
    if (ev.data === "{trick: true}") {
        // console.log("Updating trick.")
        updateTrick();
    }
}
ws.onconnecting = function (ev) {
    $("body").attr("class", 'nowebsock');
    // console.log("Closed web socket.");
}
ws.onclose = function (ev) {
    $("body").attr("class", 'nowebsock');
    ws_connected = false;
    // console.log("Closed web socket.");
}
ws.onerror = function (ev) {
    $("body").attr("class", 'nowebsock');
    ws_connected = false;
    // console.log('Websocket error occurred');
}

function updateGameData() {
    // Retrieve the JSON for game data.
    $.getJSON("/gamedata", function (result) {
        console.log("Result: " + result.game_id)
        $("div.game_info").html('');
        $("div.game_info").append("Game: " + result.game_id + "<br/>");
        $.each(result.hands, function (i, hfield) {
            $("div.game_info").append("Hand #: " + hfield.hand + "<br/>");
            $.each(hfield.teams, function (i, tfield) {
                $("div.game_info").append("Team name: " + tfield + "<br/>");
            })
            $.each(hfield.players, function (i, tfield) {
                $("div.game_info").append("Player name: " + tfield + "<br/>");
            })
        })
    })
}

function updateHand() {
    // Retrieve the JSON for prizes
    $.getJSON("/playerdeck", function (result) {
        $("div.announcement").html('');
        $("#annsection").attr("class", "hidden");
        $.each(result, function (i, field) {
            var now = new Date().getTime() / 1000;
            if (!field.hide && (field.expiration > now || field.expiration === 0)) {
                $("div.announcement").append(field.message + "<br/>");
                $("#annsection").attr("class", "unhidden");
                if (field.expiration !== 0) {
                    let sleepduration = (field.expiration - now) * 1000;
                    // console.log("Sleeping for " + sleepduration + " milliseconds.")
                    setTimeout(updateHand, sleepduration);
                }
            }
        })
    })
}

function updateTrick() {
    // Retrieve the JSON for the current trick
    $.getJSON("/trickdata", function (result) {
        $("div.prize-left").html('');
        $("div.prize-right").html('');
        $.each(result, function (i, field) {
            if (!field.hide) {
                var insert_me = "<p id='" + field.uuid + "'>"
                insert_me = insert_me + "Ticket #" + ('000000' + field.ticket).slice(-6) + " - " + field.callsign + ": " +
                    field.name + " - " + field.drawing_type
                // Alternate adding entries to each side, unless on mobile
                if (window.mobilecheck || qty_appended % 2) {
                    $("div.prize-left").append(insert_me + "</p>");
                } else {
                    $("div.prize-right").append(insert_me + "</p>");
                }
                if (field.claimed) {
                    $("#" + field.uuid).addClass("strike");
                }
                qty_appended = qty_appended + 1;
            }
        })
    })
}

function checkWidth() {
    var windowsize = $(window).width();
    if (windowsize > 768) {
        return false
    }
    return true
}

function check_ws_connected() {
    if (!ws_connected) {
        ws.open();
    }
}
$(document).ready(
    function () {
        $(".no-js").removeClass("no-js");
        window.mobilecheck = checkWidth();
        // Call each of these once on page ready.
        updateGameData();
        // updateHand();
        // updateTrick();

        // showDate();
        // Set them up as recurring events.
        // setInterval(updateAnnouncements, 5000); /* Announcement update */
        // setInterval(updatePrizes, 5000); /* Prize update */
        setInterval(check_ws_connected, 2000); /* reconnect ws? */
        // if (!window.mobilecheck) {
        //     setInterval(autoScroll, 10000); /* automatically scroll the page if it's overfull */
        // }
    },
)
/* document.ready */
