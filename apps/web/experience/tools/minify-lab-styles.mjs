import postcss from "postcss";

/** Only formatting changes: preserve declaration values, selectors and cascade. */
export function minifyLabStyles(text) {
  const root = postcss.parse(text);
  root.walk((node) => {
    if (node.type === "comment") {
      if (!/^(?:!|@license|@preserve)|copyright/i.test(node.text)) node.remove();
      return;
    }
    node.raws.before = "";
    if (node.type === "decl") {
      if (!node.prop.startsWith("--")) node.raws.between = ":";
    } else if (node.type === "rule" || node.type === "atrule") {
      node.raws.between = "";
      node.raws.after = "";
      if (node.nodes) node.raws.semicolon = false;
    }
    if (node.type === "rule") {
      node.selector = postcss.list.comma(node.selector).map((part) => part.trim()).join(",");
    }
  });
  root.raws.after = "";
  return root.toString();
}
