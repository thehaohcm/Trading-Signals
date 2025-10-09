<template>
  <div class="rrg-chart-container">
    <h2>Relative Rotation Graph (RRG)</h2>
    <div ref="chart" class="chart"></div>
  </div>
</template>

<script>
import * as d3 from 'd3';

export default {
  name: 'RRGChart',
  mounted() {
    const width = 500;
    const height = 500;
    const radius = Math.min(width, height) / 2 - 50;
    
    const svg = d3.select(this.$refs.chart)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', `translate(${width/2},${height/2})`);

    // Draw circular grid
    const numCircles = 5;
    for (let i = 0; i <= numCircles; i++) {
      svg.append('circle')
        .attr('r', (radius/numCircles) * i)
        .attr('fill', 'none')
        .attr('stroke', '#ccc');
    }

    // Draw axes
    const axisLines = 8;
    for (let i = 0; i < axisLines; i++) {
      svg.append('line')
        .attr('x1', 0)
        .attr('y1', 0)
        .attr('x2', radius * Math.cos(i * (2 * Math.PI / axisLines)))
        .attr('y2', radius * Math.sin(i * (2 * Math.PI / axisLines)))
        .attr('stroke', '#ccc')
        .attr('stroke-dasharray', '2,2');
    }

    // Sample data points
    const data = [
      { name: 'Asset A', x: 0.5, y: 0.7 },
      { name: 'Asset B', x: -0.3, y: 0.9 },
      { name: 'Asset C', x: -0.6, y: -0.2 },
      { name: 'Asset D', x: 0.8, y: -0.5 }
    ];

    // Draw data points
    svg.selectAll('.data-point')
      .data(data)
      .enter()
      .append('circle')
      .attr('class', 'data-point')
      .attr('cx', d => d.x * radius)
      .attr('cy', d => d.y * radius)
      .attr('r', 5)
      .attr('fill', 'steelblue')
      .append('title')
      .text(d => d.name);
  }
};
</script>

<style scoped>
.rrg-chart-container {
  padding: 20px;
}

.chart {
  width: 100%;
  height: 500px;
  min-width: 400px;
  min-height: 400px;
  position: relative;
  width: 100%;
  height: 500px;
  border: 1px solid #ccc;
  position: relative;
}
</style>