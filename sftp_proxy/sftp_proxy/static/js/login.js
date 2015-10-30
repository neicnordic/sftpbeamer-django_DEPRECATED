/**
 * Created by Xiaxi Li on 25/Aug/2015.
 */
$(document).ready(function() {
    var target;
    var username;
    var hostname;
    var port;

    $('.btn-connect').click(function(event) {
        event.preventDefault();
        target = $(this).attr('data-target');
        username = $('#' + target + '-username').val();
        hostname = $('#' + target + '-hostname').val();
        port = $('#' + target + '-port').val();
        if (hostname == 'host1.example.org') {
            $('#credential_modal .modal-body').html('<div class="form-group"> ' +
                '<label for="password" class="sr-only">Password</label> ' +
                '<input type="password" class="form-control" id="password" placeholder="Password"> ' +
                '</div> <div class="form-group"> <label for="otc" class="sr-only">One-time Code</label> ' +
                '<input type="text" class="form-control" id="otc" placeholder="One-time Code"/> </div>');
        } else if (hostname == 'host2.example.org') {
            $('#credential_modal .modal-body').html('<div class="form-group"> ' +
                '<label for="password" class="sr-only">Password</label> ' +
                '<input type="password" class="form-control" id="password" placeholder="Password"></div>');
        } else {
            $('#credential_modal .modal-body').html('<div class="form-group"> ' +
                '<label for="password" class="sr-only">Password</label> ' +
                '<input type="password" class="form-control" id="password" placeholder="Password"></div>');
        }
        $('#credential_modal').modal({
                keyboard: false,
                backdrop: 'static'
            });
    });

    $('#credential_submit').click(function(){
        var password;
        var otc = '';
        if (hostname == 'host1.example.org') {
            otc = $('#otc').val();
        }
        password = $('#password').val();

        var csrftoken = getCookie('csrftoken');
        $.ajax({
            type: "POST",
            url: "/sftp_proxy/dashboard/login",
            data: {"username": username, "password": password, "otc": otc, "hostname": hostname, "port": port, "source": target},
            success: function(returnedData) {
                    if (returnedData['exception']) {
                        change_modal_property("Exception", returnedData["exception"]);
                        $('#info_modal').modal({
                            keyboard: false,
                            backdrop: 'static'
                        });
                    } else if (returnedData["error"]) {
                        change_modal_property("Error", returnedData["error"]);
                        var modal = $('#info_modal');
                        modal.one('hide.bs.modal', function (event) {
                            location.reload();
                        });
                        modal.modal({
                            keyboard: false,
                            backdrop: 'static'
                        });
                    } else {
                        $("#" + target + "-path").append('<a class="' + target + '-path-link" href="/sftp_proxy/dashboard/list?path=/&source=' + target + '">/</a>');
                        $("#" + target + "-table-div").html('<table id="' + target + '-table" class="table table-striped"></table>');
                        createTable(target, returnedData["data"]);
                        $("#" + target + "-delete-btn").prop("disabled", false);
                        $("#" + target + "-transfer-btn").prop("disabled", false);
                        $("#" + target + "-disconnect-btn").prop("disabled", false);
                        $("#" + target + "-submit-btn").prop("disabled", true);
                        $("#" + target + "-username").prop("disabled", true);
                        $("#" + target + "-hostname").prop("disabled", true);
                        $("#" + target + "-port").prop("disabled", true);
                    }
                },
                dataType: "json",
                contentType: 'application/x-www-form-urlencoded; charset=utf-8',
                beforeSend: function(xhr) {
                    if (!this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", csrftoken);
                    }
                }
        });
    });
});