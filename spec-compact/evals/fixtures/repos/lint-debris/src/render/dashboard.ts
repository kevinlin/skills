import { WidgetCache, type WidgetPayload } from "../cache";

const cache = new WidgetCache();

export function renderWidget(
  widgetId: string,
  revision: number,
  readDefinition: (id: string) => WidgetPayload,
): WidgetPayload {
  const hit = cache.get(widgetId, revision);
  if (hit) return hit;
  const live = readDefinition(widgetId);
  cache.set(widgetId, revision, live);
  return live;
}
