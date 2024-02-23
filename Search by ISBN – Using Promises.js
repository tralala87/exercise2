const searchByISBN = (isbn) => {
  return new Promise((resolve, reject) => {
    // Assuming "getBookByISBN" is a function that fetches a book from a database or API
    getBookByISBN(isbn)
      .then(book => {
        resolve(book);
      })
      .catch(error => {
        reject('Error fetching book:', error);
      });
  });
};

// Usage
searchByISBN('978-3-16-148410-0')
  .then(book => {
    console.log('Fetched book:', book);
  })
  .catch(error => {
    console.error(error);
  });
