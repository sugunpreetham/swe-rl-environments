import { test, describe } from 'node:test';
import assert from 'node:assert';
import { AddWinsORSet } from '../src/crdt.ts';

describe('Task 04: AddWinsORSet CRDT Verifier', () => {

  test('Tier 1: Basic Local Add, Remove, and Query Operations', () => {
    const peer = new AddWinsORSet<string>('peer-1');
    assert.strictEqual(peer.has('doc1'), false);

    peer.add('doc1');
    assert.strictEqual(peer.has('doc1'), true);

    peer.add('doc2');
    assert.strictEqual(peer.has('doc2'), true);

    peer.remove('doc1');
    assert.strictEqual(peer.has('doc1'), false);
    assert.strictEqual(peer.has('doc2'), true);

    const elements = peer.read();
    assert.deepStrictEqual(elements, ['doc2']);
  });

  test('Tier 2: Add-Wins Semantics during Concurrent Modifications', () => {
    // Peer A and Peer B start with common element 'task-A'
    const peerA = new AddWinsORSet<string>('peer-A');
    const peerB = new AddWinsORSet<string>('peer-B');

    peerA.add('task-A');
    peerB.merge(peerA); // Both now have task-A with identical initial tag

    assert.strictEqual(peerA.has('task-A'), true);
    assert.strictEqual(peerB.has('task-A'), true);

    // Network partition occurs:
    // Peer A removes 'task-A'
    peerA.remove('task-A');
    assert.strictEqual(peerA.has('task-A'), false);

    // Peer B re-adds 'task-A' (generates a new unique tag)
    peerB.add('task-A');
    assert.strictEqual(peerB.has('task-A'), true);

    // Partition heals: A and B merge
    peerA.merge(peerB);
    peerB.merge(peerA);

    // Because Peer B's add created a new tag not observed by Peer A's removal,
    // Add-Wins guarantees 'task-A' survives!
    assert.strictEqual(peerA.has('task-A'), true, 'Add-Wins rule: concurrent add must win over remove');
    assert.strictEqual(peerB.has('task-A'), true, 'Add-Wins rule: concurrent add must win over remove');
  });

  test('Tier 3: Commutativity and Strong Eventual Consistency', () => {
    const peer1 = new AddWinsORSet<number>('node-1');
    const peer2 = new AddWinsORSet<number>('node-2');
    const peer3 = new AddWinsORSet<number>('node-3');

    peer1.add(100);
    peer2.add(200);
    peer3.add(300);

    peer1.remove(100);
    peer2.add(100); // Peer 2 concurrently adds 100

    // Clone states for asymmetric merge ordering
    const finalOrder1 = new AddWinsORSet<number>('collector-1');
    finalOrder1.merge(peer1);
    finalOrder1.merge(peer2);
    finalOrder1.merge(peer3);

    const finalOrder2 = new AddWinsORSet<number>('collector-2');
    finalOrder2.merge(peer3);
    finalOrder2.merge(peer2);
    finalOrder2.merge(peer1);

    const items1 = finalOrder1.read().sort();
    const items2 = finalOrder2.read().sort();

    assert.deepStrictEqual(items1, items2, 'State must deterministically converge regardless of merge order');
    assert.strictEqual(finalOrder1.has(100), true, '100 must be preserved via Add-Wins');
  });

  test('Tier 4: Dynamic Randomized Payload Fuzzing', () => {
    const peerX = new AddWinsORSet<string>('fuzz-X');
    const peerY = new AddWinsORSet<string>('fuzz-Y');

    const randomKeys = Array.from({ length: 50 }, (_, i) => `key_${i}_${Math.random()}`);

    for (const k of randomKeys) {
      if (Math.random() > 0.5) peerX.add(k);
      if (Math.random() > 0.5) peerY.add(k);
    }

    peerX.merge(peerY);
    peerY.merge(peerX);

    assert.deepStrictEqual(
      peerX.read().sort(),
      peerY.read().sort(),
      'Random fuzzed operations must result in bit-for-bit identical state'
    );
  });
});
