import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, FlatList, ActivityIndicator } from 'react-native';
import { Video, ResizeMode } from 'expo-av';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

import { clipsApi } from '../api';
import type { Clip } from '../types';
import type { RootStackParamList } from '../navigation/RootNavigator';

type Props = NativeStackScreenProps<RootStackParamList, 'Clips'>;

function ClipCard({ clip }: { clip: Clip }) {
  const durationSeconds = Math.round(clip.end_ts - clip.start_ts);

  return (
    <View style={styles.card}>
      {clip.playback_url ? (
        <Video
          source={{ uri: clip.playback_url }}
          style={styles.video}
          useNativeControls
          resizeMode={ResizeMode.CONTAIN}
        />
      ) : (
        <View style={[styles.video, styles.videoPlaceholder]}>
          <Text style={styles.placeholderText}>Preview unavailable</Text>
        </View>
      )}
      <View style={styles.cardFooter}>
        <Text style={styles.cardDuration}>{durationSeconds}s clip</Text>
        {clip.highlight_score !== null && (
          <Text style={styles.cardScore}>Score: {clip.highlight_score.toFixed(2)}</Text>
        )}
      </View>
    </View>
  );
}

export default function ClipsScreen({ route }: Props) {
  const { jobId } = route.params;
  const [clips, setClips] = useState<Clip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    clipsApi
      .listForJob(jobId)
      .then(setClips)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load clips'))
      .finally(() => setLoading(false));
  }, [jobId]);

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator color="#FFFFFF" size="large" />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorText}>{error}</Text>
      </View>
    );
  }

  return (
    <FlatList
      style={styles.container}
      data={clips}
      keyExtractor={(item) => item.id}
      renderItem={({ item }) => <ClipCard clip={item} />}
      contentContainerStyle={{ padding: 16 }}
      ListEmptyComponent={<Text style={styles.emptyText}>No clips were generated.</Text>}
    />
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0B0B0F' },
  centered: { flex: 1, backgroundColor: '#0B0B0F', alignItems: 'center', justifyContent: 'center' },
  card: { backgroundColor: '#17171F', borderRadius: 16, marginBottom: 16, overflow: 'hidden' },
  video: { width: '100%', aspectRatio: 9 / 16, backgroundColor: '#000000' },
  videoPlaceholder: { alignItems: 'center', justifyContent: 'center' },
  placeholderText: { color: '#6B6B76' },
  cardFooter: { flexDirection: 'row', justifyContent: 'space-between', padding: 12 },
  cardDuration: { color: '#FFFFFF', fontSize: 14, fontWeight: '600' },
  cardScore: { color: '#9A9AA5', fontSize: 13 },
  errorText: { color: '#FF6B6B' },
  emptyText: { color: '#6B6B76', textAlign: 'center', marginTop: 40 },
});
