// Build a Google Shopping search URL for an outfit item.
// We link to search results (not a specific product page) so the link always
// lands on real, in-stock, buyable products.
export function googleShoppingUrl(query) {
  return `https://www.google.com/search?tbm=shop&q=${encodeURIComponent(query)}`;
}
