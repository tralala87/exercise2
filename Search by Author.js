const searchByAuthor = (author) => {
  return new Promise((resolve, reject) => {
    // Assuming "getBooksByAuthor" is a function that fetches books from a database or API
    getBooksByAuthor(author)
      .then(books => {
        resolve(books);
      })
      .catch(error => {
        reject('Error fetching books:', error);
      });
  });
};

// Usage
searchByAuthor('John Doe')
  .then(books => {
    console.log('Fetched books:', books);
  })
  .catch(error => {
    console.error(error);
  });
