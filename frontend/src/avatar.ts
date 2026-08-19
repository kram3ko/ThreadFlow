export function avatarStyle(name: string): { background: string } {
  const hue = [...name].reduce((value, character) => value + character.charCodeAt(0), 0) % 360;
  return { background: `hsl(${hue} 55% 44%)` };
}

export function avatarInitial(name: string): string {
  return name.trim().charAt(0).toUpperCase() || "?";
}
