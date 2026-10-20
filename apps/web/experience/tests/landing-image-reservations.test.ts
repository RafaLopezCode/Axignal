import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import ts from "typescript";

function webpSize(bytes: Buffer): [number, number] {
  assert.equal(bytes.toString("ascii", 0, 4), "RIFF");
  assert.equal(bytes.toString("ascii", 8, 12), "WEBP");
  const kind = bytes.toString("ascii", 12, 16);
  if (kind === "VP8X")
    return [bytes.readUIntLE(24, 3) + 1, bytes.readUIntLE(27, 3) + 1];
  if (kind === "VP8 ")
    return [bytes.readUInt16LE(26) & 0x3fff, bytes.readUInt16LE(28) & 0x3fff];
  assert.equal(kind, "VP8L");
  const bits = bytes.readUInt32LE(21);
  return [(bits & 0x3fff) + 1, ((bits >>> 14) & 0x3fff) + 1];
}

test("Observer image reservations match the actual WebP canvas, including all method variants", () => {
  const file = new URL("../components/landing-lab.tsx", import.meta.url);
  const source = fs.readFileSync(file, "utf8");
  const tree = ts.createSourceFile(
    file.pathname,
    source,
    ts.ScriptTarget.Latest,
    true,
    ts.ScriptKind.TSX,
  );
  const steps: string[] = [];
  const images: ts.JsxSelfClosingElement[] = [];
  function visit(node: ts.Node) {
    if (
      ts.isVariableDeclaration(node) &&
      node.name.getText(tree) === "stepImages"
    ) {
      assert.ok(
        node.initializer && ts.isArrayLiteralExpression(node.initializer),
      );
      for (const entry of node.initializer.elements) {
        assert.ok(ts.isStringLiteral(entry));
        steps.push(entry.text);
      }
    }
    if (
      ts.isJsxSelfClosingElement(node) &&
      node.tagName.getText(tree) === "img"
    )
      images.push(node);
    ts.forEachChild(node, visit);
  }
  visit(tree);
  const checked = new Set<string>();
  for (const image of images) {
    const attributes = new Map(
      image.attributes.properties
        .filter(ts.isJsxAttribute)
        .map((attr) => [attr.name.getText(tree), attr.initializer]),
    );
    const src = attributes.get("src");
    let paths: string[] = [];
    if (src && ts.isStringLiteral(src) && src.text.endsWith(".webp"))
      paths = [src.text];
    else if (
      src &&
      ts.isJsxExpression(src) &&
      src.expression?.getText(tree).includes("stepImages[index]")
    )
      paths = steps.map((name) => `/marketing/${name}.webp`);
    else continue;
    const declared = ["width", "height"].map((name) => {
      const attr = attributes.get(name);
      assert.ok(
        attr &&
          ts.isJsxExpression(attr) &&
          attr.expression &&
          ts.isNumericLiteral(attr.expression),
      );
      return Number(attr.expression.text);
    });
    for (const path of paths) {
      const actual = webpSize(
        fs.readFileSync(new URL("../public" + path, import.meta.url)),
      );
      assert.deepEqual(
        declared,
        actual,
        `${path}: a lazy image must reserve its real aspect ratio`,
      );
      checked.add(path);
    }
  }
  assert.deepEqual([...checked].sort(), [
    "/marketing/explain.webp",
    "/marketing/focus.webp",
    "/marketing/memory.webp",
  ]);
});
