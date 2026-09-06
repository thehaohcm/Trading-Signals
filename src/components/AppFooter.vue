<template>
    <footer class="mt-auto text-center text-white bg-dark py-3">
      <p class="mb-2">Disclaimer: The information and indicators on this website reflect the owner's views and should not be taken as investment advice.</p>
      <p class="mb-0">Copyright © by Nguyen The Hao {{ currentYear }}. All rights reserved.</p>
    </footer>
</template>

<script>
export default {
  name: 'AppFooter',
  data() {
    return {
      currentYear: new Date().getFullYear()
    };
  }
};
</script>

<style scoped>
footer {
  width: 100%;
}
</style>