This exercise explored several ways to store, search, and analyze city coordinates.

---

## 1 – Load the GeoJSON

The data was loaded using geopandas. The dataset contains 720 unique cities.

---

## 2 – Compute distances between cities

Using the city geometries (in EPSG:32632, meters), the distances between all unique 
pairs of cities were computed and stored them in a list of dictionaries.

---

## 3 – Sort distances with two algorithms

Bubble_sort took 35 minutes to sort the distances while quick_sort took only 294 ms. 
Quick_sort proved to be significantly faster.

---

### 4 – Search for a city with two algorithms

The hash search is faster than the linear search, even including the set(cities_set) operation inside the function. 
In general the hash is much faster (O(1)) than the linear search (O(n)) for large datasets.

---
## 5 – Queue and stack search

Insert and delete operations are faster in stack than in queue, but searching for an element is equally fast in both.

---

## 6 – Graph of cities and distances

One city was selected and three of its connections and plotted this small subgraph using networkx and matplotlib.

---

7 – Plot of the graph (extra)

From the graph, we selected one city and three of its connections and plotted this small subgraph with networkx and matplotlib.
Each node represents a city and each edge is labeled with the distance, giving a simple visual check of the connectivity.

---

8 – KD-tree nearest neighbor search

A KD-tree was built from the city coordinates using scipy.spatial.KDTree.
Then I wrote a function that, given a city name, finds its nearest neighbor and returns the distance.
SciPy’s KDTree does not reveal exactly how many nodes (cities) were checked internally.