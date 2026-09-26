export interface ElementTag<T> {
  element: T;
  tag: string; // e.g. `${peerId}:${counter}:${timestamp}`
}

export class AddWinsORSet<T> {
  public readonly peerId: string;
  private counter: number;
  // Map of serialized element -> Map of tag -> ElementTag
  private addSet: Map<string, Map<string, ElementTag<T>>>;
  // Set of removed tags
  private removeSet: Set<string>;

  constructor(peerId: string) {
    if (!peerId || peerId.trim() === '') {
      throw new Error('Peer ID cannot be empty');
    }
    this.peerId = peerId;
    this.counter = 0;
    this.addSet = new Map();
    this.removeSet = new Set();
  }

  private serialize(elem: T): string {
    return JSON.stringify(elem);
  }

  /**
   * Adds an element to the local set and generates a unique tag.
   */
  public add(element: T): string {
    this.counter += 1;
    const tag = `${this.peerId}:${this.counter}:${Date.now()}`;
    const key = this.serialize(element);

    if (!this.addSet.has(key)) {
      this.addSet.set(key, new Map());
    }

    this.addSet.get(key)!.set(tag, { element, tag });
    return tag;
  }

  /**
   * Removes an element by adding all currently observed tags for that element
   * to the removeSet (tombstones).
   */
  public remove(element: T): void {
    const key = this.serialize(element);
    const tagsMap = this.addSet.get(key);
    if (!tagsMap) return;

    for (const tag of tagsMap.keys()) {
      this.removeSet.add(tag);
    }
  }

  /**
   * Checks whether the element currently exists in the set.
   * Add-Wins semantics: True if at least one tag exists in addSet that is NOT in removeSet.
   */
  public has(element: T): boolean {
    const key = this.serialize(element);
    const tagsMap = this.addSet.get(key);
    if (!tagsMap || tagsMap.size === 0) return false;

    for (const tag of tagsMap.keys()) {
      if (!this.removeSet.has(tag)) {
        return true;
      }
    }
    return false;
  }

  /**
   * Returns all active elements in the set.
   */
  public read(): T[] {
    const result: T[] = [];
    for (const [, tagsMap] of this.addSet.entries()) {
      for (const [tag, item] of tagsMap.entries()) {
        if (!this.removeSet.has(tag)) {
          result.push(item.element);
          break; // One active tag is sufficient to include the element
        }
      }
    }
    return result;
  }

  /**
   * Merges incoming state from another peer.
   * Guarantees Commutative, Associative, and Idempotent convergence.
   */
  public merge(remote: AddWinsORSet<T>): void {
    // 1. Union removeSets (tombstones are monotonically accumulated)
    for (const tag of remote.removeSet) {
      this.removeSet.add(tag);
    }

    // 2. Union addSets
    for (const [key, remoteTagsMap] of remote.addSet.entries()) {
      if (!this.addSet.has(key)) {
        this.addSet.set(key, new Map());
      }
      const localTagsMap = this.addSet.get(key)!;
      for (const [tag, elementTag] of remoteTagsMap.entries()) {
        if (!localTagsMap.has(tag)) {
          localTagsMap.set(tag, elementTag);
        }
      }
    }

    // Update counter to avoid tag collisions if peerIds were identical (defensive)
    this.counter = Math.max(this.counter, remote.counter);
  }

  public getRawState() {
    return {
      peerId: this.peerId,
      adds: Array.from(this.addSet.entries()).map(([k, v]) => [k, Array.from(v.keys())]),
      removes: Array.from(this.removeSet),
    };
  }
}
