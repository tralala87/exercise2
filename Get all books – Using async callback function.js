const getAllBooks = async (callback) => {
  try {
    // Assuming "getBooks" is a function that fetches all books from a database or API
    const books = await getBooks();

    // Call the callback function with the books data
    callback(null, books);
  } catch (error) {
    // If there's an error, call the callback with the error message
    callback(error);
  }
};

// Usage
getAllBooks((error, books) => {
  if (error) {
    console.error('Error fetching books:', error);
  } else {
    console.log('Fetched books:', books);
  }
});
