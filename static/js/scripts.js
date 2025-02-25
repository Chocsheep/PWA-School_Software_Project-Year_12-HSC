function sortMovies(order) {
    $.ajax({
        url: '/sort_movie',
        type: 'POST',
        data: { order: order },
        success: function(response) {
            // Update the movie list with the sorted movies
            var movieList = $('#movie-list');
            movieList.empty();
            response.forEach(function(movie) {
                var stars = '';
                for (var i = 0; i < Math.floor(movie.rating / 2); i++) {
                    stars += '<span class="fa fa-star checked"></span>';
                }
                var movieHtml = `
                    <div class="movie-container">
                        <img src="/static/images/${movie.id}.jpg" alt="${movie.name} poster" class="movie-poster">
                        <div class="movie-details">
                            <h3 class="title">${movie.name}</h3>
                            <div class="stars">
                                ${stars}
                            </div>
                            <p>Rating: ${movie.rating} / 10</p>
                        </div>
                    </div>
                `;
                movieList.append(movieHtml);
            });
        },
        error: function(error) {
            console.log("Error sorting movies");
        }
    });
}