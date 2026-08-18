// ABOUTME: Default dependency-cruiser config — extends the recommended baseline for
// ABOUTME: cycle detection and dependency hygiene. A starting point; tune per project.
module.exports = {
  extends: 'dependency-cruiser/configs/recommended',
  options: {
    // Resolve TypeScript path aliases from the project's tsconfig so first-party
    // imports don't read as unresolvable. Repoint or remove if there is no tsconfig.
    tsConfig: { fileName: 'tsconfig.json' }
  }
};
