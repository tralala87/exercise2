const searchByTitle = (title) => {
  return new Promise((resolve, reject) => {
    // Assuming "getBooksByTitle" is a function that fetches books from a database or API
    getBooksByTitle(title)
      .then(books => {
        resolve(books);
      })
      .catch(error => {
        reject('Error fetching books:', error);
      });
  });
};

// Usage
searchByTitle('Book Title')
  .then(books => {
    console.log('Fetched books:', books);
  })
  .catch(error => {
    console.error(error);
  });
