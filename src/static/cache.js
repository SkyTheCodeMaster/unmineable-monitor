// Manually update the cache.
function updateCache() {
  console.log("Cache button clicked");
  var xhr = new XMLHttpRequest();
  xhr.open("POST","api/updatecache");
  xhr.send();
  location.reload();
}