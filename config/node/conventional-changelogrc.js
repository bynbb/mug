// .conventional-changelogrc.js
const TYPE_PREFIX_RE =
  /^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(!:)?(\([^)]+\))?:\s*/i;
const MD_LINK_RE = /\[([^\]]*?)\]\((?:[^)]+)\)/g;

module.exports = {
  writerOpts: {
    // Never autolink issues/PRs
    linkReferences: false,

    // Render exactly the two sections we want, with "none" fallbacks
    mainTemplate: [
      '## {{#if version}}{{version}}{{else}}0.0.0{{/if}} ({{date}})',
      '',
      '#### Features',
      '{{#if features.length}}',
      '{{#each features}}* {{#if scope}}**{{scope}}:** {{/if}}{{subject}}',
      '{{/each}}',
      '{{else}}* none',
      '{{/if}}',
      '',
      '#### Fixes',
      '{{#if fixes.length}}',
      '{{#each fixes}}* {{#if scope}}**{{scope}}:** {{/if}}{{subject}}',
      '{{/each}}',
      '{{else}}* none',
      '{{/if}}',
      ''
    ].join('\n'),

    // Build the `features` and `fixes` arrays for the template
    finalizeContext: (context, writerOpts, commits) => {
      const features = [];
      const fixes = [];
      for (const c of commits) {
        if (c && c.type === 'Features') features.push(c);
        else if (c && c.type === 'Fixes') fixes.push(c);
      }
      context.features = features;
      context.fixes = fixes;
      return context;
    },

    // Keep only feat/fix; strip tag prefixes and any markdown links
    transform: (c) => {
      if (!c) return;
      const commit = { ...c, hash: null, references: [] };

      // map Angular types to our section names
      if (commit.type === 'feat') commit.type = 'Features';
      else if (commit.type === 'fix') commit.type = 'Fixes';
      else return; // drop every other type (docs/chore/ci/etc.)

      if (typeof commit.subject === 'string') {
        let s = commit.subject.replace(TYPE_PREFIX_RE, ''); // drop "feat:" / "fix(scope):"
        s = s.replace(MD_LINK_RE, '$1').trim();            // strip any [text](url)
        commit.subject = s;
      }

      // also scrub notes just in case (BREAKING CHANGE)
      if (Array.isArray(commit.notes)) {
        commit.notes = commit.notes.map(n => ({
          ...n,
          text: typeof n.text === 'string' ? n.text.replace(MD_LINK_RE, '$1') : n.text
        }));
      }
      return commit;
    }
  }
};