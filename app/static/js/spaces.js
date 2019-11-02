var btn = document.getElementById("myBtn");
var space = document.getElementById("space");
var content = document.getElementById("content");
var warning = document.getElementById("warning");
var PATTERN = document.getElementById("filter");
var filter_btn = document.getElementById("filter_btn");

function myFn(){
    if (filter_btn.innerHTML == "Apply Filter"){
        var myOptions = space.options;
        var numberofitems = myOptions.length;
        var optionHTML = '';
        var i;
        for (i=1;i<=numberofitems;i++){
            var Option_Text = (myOptions[i-1].innerText);
            var myOptionValue = myOptions[i-1].value;
            if (Option_Text.includes(PATTERN.value)){
                optionHTML += '<option value="' + myOptionValue + '">' + Option_Text + '</option>';
            }
        }
        space.innerHTML = optionHTML;
        filter_btn.innerHTML = "Remove Filter";
        filter_btn.setAttribute("class", "btn btn-warning btn-block");
    }
    else {
        window.location.reload()
    }
}

btn.onclick = function() {
    spaceID = space.value;
    console.log(spaceID.length);
    if(spaceID.length == 0){
        document.getElementById("spinner").style.display = "none";
        warning.innerHTML = "Select a space to see the active members.";
        }
    else {
        document.getElementById("spinner").style.display = "";
        warning.innerHTML = '';
        while(content.hasChildNodes())
            {
            content.removeChild(content.firstChild);
            }
        spaceId = space.value;    
        fetch('/member_details/' + spaceId).then(function(response) {
        response.json().then(function(data) {
            document.getElementById("spinner").style.display = "none";
            for (var user of data.members) {
                var listItem = document.createElement('li');
                listItem.setAttribute('class','list-group-item');
                listItem.innerHTML = ((user.DisplayName) + " - " + (user.Email));
                content.appendChild(listItem);
                }
            })
        });
    }
}