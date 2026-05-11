/*
 * Example Alpine.js component.
 *
 * Reach for Alpine ONLY when:
 * - Interaction is purely client-side (no server data needed)
 * - HTMX would force a roundtrip for something that doesn't need one
 * - The state is non-trivial (multiple toggles, conditional UI)
 *
 * For simple show/hide, prefer <details>/<summary> — zero JS.
 * For anything fetching data, prefer HTMX.
 *
 * Reference for:
 * - x-data with local state
 * - Computed properties via getters
 * - Methods for behavior
 * - Re-binding after HTMX swap (htmx:afterSwap listener)
 */

// ─── Component: copy-to-clipboard button ────────────────────────────────────
// Usage in template:
//
//   <div x-data="copyButton('text to copy')">
//     <button @click="copy()" :class="{ 'bg-green-100': copied }">
//       <span x-text="copied ? 'Copied!' : 'Copy'"></span>
//     </button>
//   </div>

window.copyButton = function (text) {
  return {
    copied: false,
    async copy() {
      try {
        await navigator.clipboard.writeText(text);
        this.copied = true;
        setTimeout(() => (this.copied = false), 2000);
      } catch (err) {
        console.error("Clipboard write failed:", err);
      }
    },
  };
};

// ─── Component: tag input with chips ────────────────────────────────────────
// Pure client-side until the form submits. Server validates on submit.
//
//   <div x-data="tagInput(['initial', 'tags'])">
//     <input type="hidden" name="tags" :value="tags.join(',')">
//     <div class="flex flex-wrap gap-1">
//       <template x-for="(tag, i) in tags" :key="tag">
//         <span class="badge">
//           <span x-text="tag"></span>
//           <button type="button" @click="remove(i)" aria-label="Remove">×</button>
//         </span>
//       </template>
//     </div>
//     <input
//       type="text"
//       x-model="draft"
//       @keydown.enter.prevent="add()"
//       @keydown.backspace="draft === '' && tags.length && remove(tags.length - 1)"
//       placeholder="Type a tag, press Enter">
//   </div>

window.tagInput = function (initial = []) {
  return {
    tags: [...initial],
    draft: "",
    add() {
      const value = this.draft.trim();
      if (!value || this.tags.includes(value)) {
        this.draft = "";
        return;
      }
      this.tags.push(value);
      this.draft = "";
    },
    remove(index) {
      this.tags.splice(index, 1);
    },
  };
};

// ─── Component: collapsible disclosure with state persistence ──────────────
// Use <details>/<summary> when persistence isn't needed.
// This version persists open/closed via local component state (not localStorage).
//
//   <div x-data="disclosure(false)">
//     <button @click="toggle()" :aria-expanded="open">More options</button>
//     <div x-show="open" x-cloak>...</div>
//   </div>

window.disclosure = function (initialOpen = false) {
  return {
    open: initialOpen,
    toggle() {
      this.open = !this.open;
    },
  };
};

// ─── HTMX integration: re-init Alpine after content swap ────────────────────
// Alpine auto-initializes new x-data nodes on DOMContentLoaded.
// When HTMX swaps new content in, Alpine doesn't see it automatically
// unless you use Alpine v3.x + alpine-morph, or trigger init manually.

document.body.addEventListener("htmx:afterSwap", (event) => {
  if (window.Alpine && typeof window.Alpine.initTree === "function") {
    window.Alpine.initTree(event.detail.target);
  }
});

// ─── Anti-patterns to avoid ────────────────────────────────────────────────
//
// ❌ Fetching data with Alpine — use HTMX instead:
//
//      x-data="{ orders: [], load() { fetch('/api/orders').then(...) } }"
//
//    Wrong: now you have two ways to render data (server templates + Alpine).
//    Right: hx-get="/orders/" hx-trigger="load" hx-target="#order-list"
//
// ❌ Replicating server state in Alpine:
//
//      x-data="{ user: { name: '{{ request.user.first_name }}' } }"
//
//    The template already has access to request.user. Don't duplicate.
//
// ❌ Using Alpine for a 1-line interaction <details> would handle:
//
//      <div x-data="{ open: false }">
//        <button @click="open = !open">Show</button>
//        <div x-show="open">...</div>
//      </div>
//
//    vs
//
//      <details>
//        <summary>Show</summary>
//        <div>...</div>
//      </details>
//
//    The second one needs no JS, no framework, and has built-in keyboard
//    handling and aria-expanded.
