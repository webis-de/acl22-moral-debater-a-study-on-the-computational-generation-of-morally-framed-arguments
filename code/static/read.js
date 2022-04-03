$(document).ready(function() {
});

function start_submit(){
  // input = prepare_input();

  let moral_array = [];
  let input_string='';
  
  
  query_size = document.getElementById('size');
  stance_pro = document.getElementById('pro');
  stance_con = document.getElementById('con');
  

  claim_value = document.getElementById('claim_area').value;
  evidence_value = document.getElementById('evidence_area').value;

  if(claim_value > 1){
    // pass the default value
    claim_value = 0.8
  }
  
  if(evidence_value>1){
    // pass the default value
    evidence_value = 0.6
  }


  if(moral1.checked){moral_array.push(moral1.name); input_string=input_string+moral1.value;}
  if(moral2.checked){moral_array.push(moral2.name); input_string=input_string+'_'+moral2.value;}
  if(moral3.checked){moral_array.push(moral3.name); input_string=input_string+'_'+moral3.value;}
  if(moral4.checked){moral_array.push(moral4.name); input_string=input_string+'_'+moral4.value;}
  if(moral5.checked){moral_array.push(moral5.name); input_string=input_string+'_'+moral5.value;}

  // this will comprise of the topic, pro or con stance and query size
  var text_string = document.getElementById('topics').value;
  
  // stance added in text string
  if(stance_pro.checked){ text_string=text_string+'_'+stance_pro.value;}
  if(stance_con.checked){ text_string=text_string+'_'+stance_con.value;} 
  
  // query size added in text string
  text_string=text_string+'_'+query_size.value;
    
  text_string = text_string + '_' + claim_value + '_' +evidence_value;
    
  
  $("#progressbar").attr("hidden", false)
  $('#gen_btn').attr("disabled", true)
  

  var result = document.getElementById("argument_area");
  result.value= '';

  const request = new XMLHttpRequest();
  request.open('GET','/submit/'+input_string+'$'+text_string);
  
  request.onreadystatechange = function () {
      $("#progressbar").attr("hidden", true)
      $('#gen_btn').attr("disabled", false)

      // In local files, status is 0 upon success in Mozilla Firefox
      if(request.readyState === XMLHttpRequest.DONE) {
        var status = request.status;
        if (status === 0 || (status >= 200 && status < 400)) {
          // The request has been completed successfully
          var result = document.getElementById("argument_area");
          result.value= request.responseText;
          console.log('request completed');
        } else {
          // Oh no! There has been an error with the request!
        }
      }
    };

  request.send()
  
  return true
  
}