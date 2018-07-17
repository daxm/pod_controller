function eventListeners(){
  document.getElementById("thing1").addEventListener("click", function(){
    alert("hi");
    window.location.href = "http://www.daxm.net";
  });

  document.getElementById("daxm").addEventListener("click", function(){
    alert("hi");
    window.location.href = "http://www.daxm.net";
  });
};

// Wait until the document is ready
document.addEventListener("DOMContentLoaded", function(){
  eventListeners();
});

