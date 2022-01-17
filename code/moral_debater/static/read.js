function start_submit(){
  // input = prepare_input();

  let moral_array = [];
  let input_string='';
  
  reqstatus = document.getElementById('reqprocessed');
  reqstatus.innerHTML='process started';
  moral1=document.getElementById('moral1');
  moral2=document.getElementById('moral2');
  moral3=document.getElementById('moral3');
  moral4=document.getElementById('moral4');
  moral5=document.getElementById('moral5');
  
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


  if(moral1.checked){moral_array.push(moral1.name); input_string=input_string+moral1.name;}
  if(moral2.checked){moral_array.push(moral2.name); input_string=input_string+'_'+moral2.name;}
  if(moral3.checked){moral_array.push(moral3.name); input_string=input_string+'_'+moral3.name;}
  if(moral4.checked){moral_array.push(moral4.name); input_string=input_string+'_'+moral4.name;}
  if(moral5.checked){moral_array.push(moral5.name); input_string=input_string+'_'+moral5.name;}
  
  // this will comprise of the topic, pro or con stance and query size
  var text_string = document.getElementById('topics').value;
  
  // stance added in text string
  if(stance_pro.checked){ text_string=text_string+'_'+stance_pro.value;}
  if(stance_con.checked){ text_string=text_string+'_'+stance_con.value;} 
  
  // query size added in text string
  text_string=text_string+'_'+query_size.value;
    
  text_string = text_string + '_' + claim_value + '_' +evidence_value;
    


  const request = new XMLHttpRequest();
  request.open('GET','/submit/'+input_string+'$'+text_string);
  
  request.onreadystatechange = function () {
      // In local files, status is 0 upon success in Mozilla Firefox
      if(request.readyState === XMLHttpRequest.DONE) {
        var status = request.status;
        if (status === 0 || (status >= 200 && status < 400)) {
          // The request has been completed successfully
          var result = document.getElementById("resultsArea");
          result.value= request.responseText;
          reqstatus.innerHTML='process completed'; 
          console.log('request completed');
        } else {
          // Oh no! There has been an error with the request!
        }
      }
    };

  request.send()
    
  
}