function FilterInput(event) {
    var keyCode = ('which' in event) ? event.which : event.keyCode;

    isNotWanted = (keyCode == 69 || keyCode == 101);
    return !isNotWanted;
};

function handlePaste (e) {
    var clipboardData, pastedData;

    // Get pasted data via clipboard API
    clipboardData = e.clipboardData || window.clipboardData;
    pastedData = clipboardData.getData('Text').toUpperCase();

    if(pastedData.indexOf('E')>-1) {
        //alert('found an E');
        e.stopPropagation();
        e.preventDefault();
    }
};

function toProgressBar(val,name) {
		var progBar = document.getElementById(name + "progress");
		progBar.style.width = val + "%";
		progBar.innerHtml = val + "%";
};
$(document).ready (function(){
	$(".click-alerts").hide();
});


$('.pforms, .aforms').on('submit', function(e){   // fire on submit
    e.preventDefault();
	var form = $(this);
	var formData = new FormData(form[0]);
	var cName = $(this).attr('class');
	cName = cName.slice(cName.indexOf(" "), cName.length).trim();
	formData.append('classname', cName);
	var ajaxObj ={
		type: "POST",
		url: "/post_json/",
		data: formData,
		processData: false,
		contentType: false,
		
        // handle a successful response
        success : function(json) {
			if(json.success == true){
				$(".click-alerts").show();
				$(".click-alerts").delay(2000).slideUp(500, function(){
					$(".click-alerts").hide();
				});
			}
            console.log(json.success); // log the returned json to the console
            console.log("success"); // another sanity check
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
	};
	
    $.ajax(ajaxObj).done(function(request){
	});
	
	

});

