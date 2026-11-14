/* The Resistance Explorer views: each is its own page under /explore/<key>,
   listed in the navbar's Insights menu with a one-line hint */
export const EXPLORE_VIEWS = [
  { key: 'heatmap', label: 'Country heat map', icon: 'bi-globe2', hint: 'Resistant % in each country' },
  { key: 'dominant', label: 'Dominant resistance', icon: 'bi-palette', hint: 'Top resistance type per country' },
  { key: 'map', label: 'Map by antibiotic group', icon: 'bi-map', hint: 'One drug group across the world' },
  { key: 'groups', label: 'Group-wise comparison', icon: 'bi-bar-chart', hint: 'Families, organisms, infection types' },
  { key: 'drugs', label: 'Drug-wise comparison', icon: 'bi-capsule', hint: 'Drugs side by side, yearly trend' },
  { key: 'chemistry', label: 'Chemistry', icon: 'bi-hexagon', hint: 'Resistance by chemical group' },
];
