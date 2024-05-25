document.querySelector('.fab.fa-discord').parentElement.parentElement.addEventListener('click', function() {
    var Name = "KenkiCZ";
    navigator.clipboard.writeText(Name)
        .then(function() {
            showPopover("Name has been copied!");
        })
        .catch(function(error) {
            console.error('Error copying text: ', error);
        });
});

function showPopover(message) {
    var popover = document.getElementById('popover');
    popover.textContent = message;
    popover.style.display = 'block';
    setTimeout(function() {
        popover.style.display = 'none';
    }, 1500); // Adjust the duration as needed
}
