$(document).ready(function() {

    // Function to animate the search bar
    function animateSearchBar() {
        let searchBar = $('input[name="search_text"]');

        searchBar.animate({
            width: "toggle",
        }, 500, function() {
            // Callback after animation.
            // Will start another animation in this case.
            searchBar.animate({
                width: "toggle",
            }, 500);
        });
    }

    // Start the animation as soon as the page loads.
    animateSearchBar();

    $(window).on('load', function() {
        setTimeout(function() {
            $('#loading-screen').fadeOut('slow', function() {
                $(this).remove();
            });
        }, 10000); // 10000ms = 10s
    });


});