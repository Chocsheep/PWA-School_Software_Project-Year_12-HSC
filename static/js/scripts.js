function sortMovies(order) {
    $.ajax({
        url: '/sort_movie', // url that the function will send the request to
        type: 'POST', // type of request
        data: { order: order }, // data to send in the request (in this case, the order)
                                // also can be rewritten as "order": order (sending to the request form "order in app.py")
        success: function(response) { // once the server processes the request and sends a response,
                                      // jQuery's $.ajax function automatically handles the response, if it is a success:
            // Update the movie list with the rendered HTML
            var movieList = $('#movie-list'); // $ is a shortcut for jQuery, selecting the element with the id "movie-list"
            movieList.html(response.html); // updating the HTML of the movie list with the response from the server
        },
        error: function(error) { // if the server returns an error, this function will be called
            console.log("Error sorting movies"); // logs error message to the console
        }
    });
}