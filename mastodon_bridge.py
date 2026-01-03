#!/usr/bin/env python3
"""
Mastodon-Community-Bridge
Findet thematisch verwandte Posts und Nutzer über Instanz-Grenzen hinweg
"""

import requests
import json
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import time
import argparse
import sys


class MastodonBridge:
    def __init__(self, instances, min_similarity=0.3):
        """
        instances: Liste von Mastodon-Instanzen (z.B. ['mastodon.social', 'chaos.social'])
        min_similarity: Minimale Ähnlichkeit (0-1) für Vorschläge
        """
        self.instances = instances
        self.min_similarity = min_similarity
        self.posts_data = []

    def fetch_public_timeline(self, instance, limit=40):
        """Holt öffentliche Timeline einer Instanz"""
        url = f"https://{instance}/api/v1/timelines/public"
        params = {'limit': limit, 'local': True}

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Fehler bei {instance}: {e}")
            return []

    def extract_keywords(self, text):
        """Extrahiert relevante Keywords aus Text"""
        if not text:
            return set()

        # Einfache Keyword-Extraktion (lowercase, min 4 Zeichen)
        words = text.lower().split()
        keywords = {w.strip('.,!?;:()[]{}') for w in words
                    if len(w) > 3 and not w.startswith('http')}
        return keywords

    def extract_hashtags(self, post):
        """Extrahiert Hashtags aus Post"""
        if 'tags' in post:
            return {tag['name'].lower() for tag in post['tags']}
        return set()

    def calculate_similarity(self, post1, post2):
        """Berechnet Ähnlichkeit zwischen zwei Posts (0-1)"""
        # Hashtags haben höheres Gewicht
        tags1 = self.extract_hashtags(post1)
        tags2 = self.extract_hashtags(post2)

        # Keywords aus Content
        content1 = post1.get('content', '').replace('<p>', ' ').replace('</p>', ' ')
        content2 = post2.get('content', '').replace('<p>', ' ').replace('</p>', ' ')

        words1 = self.extract_keywords(content1)
        words2 = self.extract_keywords(content2)

        # Ähnlichkeit berechnen
        if not tags1 and not tags2 and not words1 and not words2:
            return 0

        tag_overlap = len(tags1 & tags2)
        word_overlap = len(words1 & words2)

        # Gewichtete Ähnlichkeit
        tag_sim = (tag_overlap / max(len(tags1 | tags2), 1)) * 2  # Doppeltes Gewicht
        word_sim = word_overlap / max(len(words1 | words2), 1)

        return min((tag_sim + word_sim) / 3, 1.0)

    def collect_data(self):
        """Sammelt Daten von allen Instanzen"""
        print("📡 Sammle Daten von Instanzen...")

        for instance in self.instances:
            print(f"  ⏳ {instance}...", end=' ')
            posts = self.fetch_public_timeline(instance)

            for post in posts:
                self.posts_data.append({
                    'instance': instance,
                    'post': post,
                    'account': post.get('account', {}),
                    'url': post.get('url', '')
                })

            print(f"✅ {len(posts)} Posts")
            time.sleep(1)  # Rate limiting

        print(f"\n✨ Insgesamt {len(self.posts_data)} Posts gesammelt\n")

    def find_bridges(self):
        """Findet thematische Brücken zwischen Instanzen"""
        bridges = []

        print("🔍 Suche thematische Verbindungen...\n")

        # Vergleiche Posts von verschiedenen Instanzen
        for i, data1 in enumerate(self.posts_data):
            for data2 in self.posts_data[i + 1:]:
                # Nur Posts von verschiedenen Instanzen vergleichen
                if data1['instance'] == data2['instance']:
                    continue

                similarity = self.calculate_similarity(data1['post'], data2['post'])

                if similarity >= self.min_similarity:
                    bridges.append({
                        'similarity': similarity,
                        'post1': data1,
                        'post2': data2,
                        'common_tags': self.extract_hashtags(data1['post']) &
                                       self.extract_hashtags(data2['post'])
                    })

        # Sortiere nach Ähnlichkeit
        bridges.sort(key=lambda x: x['similarity'], reverse=True)
        return bridges

    def print_bridges(self, bridges, max_results=10):
        """Gibt gefundene Brücken aus"""
        if not bridges:
            print("❌ Keine thematischen Verbindungen gefunden.")
            print("💡 Tipp: Reduziere --min-similarity oder füge mehr Instanzen hinzu\n")
            return

        print(f"🌉 {len(bridges)} Thematische Brücken gefunden!\n")
        print("=" * 80)

        for i, bridge in enumerate(bridges[:max_results], 1):
            acc1 = bridge['post1']['account']
            acc2 = bridge['post2']['account']

            print(f"\n🔗 Brücke #{i} (Ähnlichkeit: {bridge['similarity']:.0%})")
            print(f"   Gemeinsame Tags: {', '.join(bridge['common_tags']) or 'keine'}")
            print()

            # Post 1
            content1 = bridge['post1']['post'].get('content', '')[:150].replace('<p>', '').replace('</p>', ' ')
            print(f"   📍 {bridge['post1']['instance']}")
            print(f"   👤 @{acc1.get('username')} ({acc1.get('display_name', 'Unbekannt')})")
            print(f"   💬 {content1}...")
            print(f"   🔗 {bridge['post1']['url']}")
            print()

            # Post 2
            content2 = bridge['post2']['post'].get('content', '')[:150].replace('<p>', '').replace('</p>', ' ')
            print(f"   📍 {bridge['post2']['instance']}")
            print(f"   👤 @{acc2.get('username')} ({acc2.get('display_name', 'Unbekannt')})")
            print(f"   💬 {content2}...")
            print(f"   🔗 {bridge['post2']['url']}")

            print("   " + "-" * 76)

        if len(bridges) > max_results:
            print(f"\n... und {len(bridges) - max_results} weitere Verbindungen")
        print("\n" + "=" * 80)

    def generate_discovery_digest(self, bridges, output_file=None):
        """Erstellt einen Discovery Digest"""
        if not bridges:
            return

        digest = {
            'generated_at': datetime.now().isoformat(),
            'instances': self.instances,
            'total_bridges': len(bridges),
            'top_connections': []
        }

        for bridge in bridges[:20]:
            digest['top_connections'].append({
                'similarity': bridge['similarity'],
                'instance1': bridge['post1']['instance'],
                'instance2': bridge['post2']['instance'],
                'user1': bridge['post1']['account'].get('acct'),
                'user2': bridge['post2']['account'].get('acct'),
                'url1': bridge['post1']['url'],
                'url2': bridge['post2']['url'],
                'common_tags': list(bridge['common_tags'])
            })

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(digest, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Discovery Digest gespeichert: {output_file}")

        return digest

    def get_instance_stats(self):
        """Zeigt Statistiken zu den Instanzen"""
        stats = defaultdict(lambda: {'posts': 0, 'users': set(), 'hashtags': Counter()})

        for data in self.posts_data:
            instance = data['instance']
            stats[instance]['posts'] += 1
            stats[instance]['users'].add(data['account'].get('acct'))

            for tag in self.extract_hashtags(data['post']):
                stats[instance]['hashtags'][tag] += 1

        print("\n📊 Instanz-Statistiken:")
        print("=" * 80)
        for instance, stat in stats.items():
            print(f"\n📍 {instance}")
            print(f"   Posts: {stat['posts']}")
            print(f"   Aktive Nutzer: {len(stat['users'])}")
            top_tags = stat['hashtags'].most_common(3)
            if top_tags:
                print(f"   Top Hashtags: {', '.join(f'#{t[0]} ({t[1]})' for t in top_tags)}")
        print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description='Mastodon-Community-Bridge: Finde thematische Verbindungen zwischen Instanzen',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s mastodon.social chaos.social
  %(prog)s mastodon.social fosstodon.org -s 0.4 -n 15
  %(prog)s mastodon.social chaos.social --stats --output digest.json
        """
    )

    parser.add_argument('instances', nargs='+',
                        help='Mastodon-Instanzen (ohne https://)')
    parser.add_argument('-s', '--min-similarity', type=float, default=0.3,
                        help='Minimale Ähnlichkeit (0-1, Standard: 0.3)')
    parser.add_argument('-n', '--max-results', type=int, default=10,
                        help='Max. Anzahl Ergebnisse (Standard: 10)')
    parser.add_argument('--stats', action='store_true',
                        help='Zeige Instanz-Statistiken')
    parser.add_argument('-o', '--output',
                        help='Speichere Discovery Digest als JSON')

    args = parser.parse_args()

    # Validierung
    if args.min_similarity < 0 or args.min_similarity > 1:
        print("❌ Fehler: min-similarity muss zwischen 0 und 1 liegen")
        sys.exit(1)

    if len(args.instances) < 2:
        print("❌ Fehler: Mindestens 2 Instanzen erforderlich")
        sys.exit(1)

    # Banner
    print("\n" + "=" * 80)
    print("🌉 Mastodon-Community-Bridge")
    print("   Finde thematische Verbindungen über Instanz-Grenzen hinweg")
    print("=" * 80 + "\n")

    # Bridge erstellen und ausführen
    bridge = MastodonBridge(args.instances, args.min_similarity)
    bridge.collect_data()

    if args.stats:
        bridge.get_instance_stats()

    bridges = bridge.find_bridges()
    bridge.print_bridges(bridges, args.max_results)

    if args.output:
        bridge.generate_discovery_digest(bridges, args.output)

    print()


if __name__ == "__main__":
    main()