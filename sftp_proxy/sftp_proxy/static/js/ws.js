/**
 * Created by Xiaxi Li on 14/Jul/2015.
 */

function create_ws_channel() {
    var transport = WebSocket;

// Receive the path for the connection from the django template context:
    var endpoint = 'ws://localhost:4242/ec';

// Create a new connection using transport, endpoint and options
    var connection = new Omnibus(transport, endpoint);
    var channel = connection.openChannel('progress');


    var transferred_file_name = $('#transferred-file-name');
    var progress_bar = $('#transferred-file-progress-bar');
    channel.on('update', function (event) {
        transferred_file_name.text(event.data.payload.file_name);
        var transferred_bytes = event.data.payload.transferred_bytes;
        var total_bytes = event.data.payload.total_bytes;
        if (transferred_bytes == total_bytes) {
            progress_bar.text('100%');
            progress_bar.css("width", '100%');
        } else {
            var percentage = Math.round(transferred_bytes / total_bytes) * 100;
            progress_bar.text(percentage + '%');
            progress_bar.css("width", percentage + '%');
        }
    });

    return channel;
}
