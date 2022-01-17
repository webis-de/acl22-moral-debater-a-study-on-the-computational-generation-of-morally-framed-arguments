function start_submit(){
    // input = prepare_input();

    let moral_array = [];
    moral1=document.getElementById('moral1');
    moral2=document.getElementById('moral2');
    moral3=document.getElementById('moral3');
    moral4=document.getElementById('moral4');
    moral5=document.getElementById('moral5');

    if(moral1.checked){moral_array.push(moral1.name)}
    if(moral2.checked){moral_array.push(moral2.name)}
    if(moral3.checked){moral_array.push(moral3.name)}
    if(moral4.checked){moral_array.push(moral4.name)}
    if(moral5.checked){moral_array.push(moral5.name)}

    var text = document.getElementById('topics').value;
    var claim_threshold = document.getElementById('claim').value;
    var evidence_threshold = document.getElementById('evidence').value;

    var result = document.getElementById("resultsArea");

    result.value = "morals are: " + moral_array + ' and the text was: ' +text;

}
