import { useEffect, useMemo, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, ScrollView } from 'react-native';
import { api, TankStatus, BackendRecommendation } from '../lib/api';

export default function Index() {
  const [tank, setTank] = useState<TankStatus | null>(null);
  const [reco, setReco] = useState<BackendRecommendation | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = async () => {
    setLoading(true);
    try {
      const [t, r] = await Promise.all([
        api.tankStatus('T1').catch(() => null),
        api.recoRecent('Z1', 1).then(x => x.items?.[0] as any).catch(() => null),
      ]);
      setTank(t);
      setReco(r);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 15000);
    return () => clearInterval(id);
  }, []);

  const quickStart = async (seconds: number) => {
    try {
      await api.irrigationStart('Z1', seconds);
      await refresh();
    } catch {}
  };

  const stop = async () => {
    try { await api.irrigationStop('Z1'); await refresh(); } catch {}
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>AgriSense</Text>
      {loading && <ActivityIndicator size="small" />}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Tank</Text>
        <Text>Level: {tank?.level_pct != null ? `${tank.level_pct.toFixed(0)}%` : '—'}</Text>
        <Text>Volume: {tank?.volume_l != null ? `${Math.round(tank.volume_l)} L` : '—'}</Text>
        <Text>Updated: {tank?.last_update ? new Date(tank.last_update).toLocaleTimeString() : '—'}</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Last Recommendation</Text>
        <Text>Water (L): {reco?.water_liters ?? '-'}</Text>
        <Text>Water source: {reco?.water_source ?? '-'}</Text>
        <Text>Runtime (min): {reco?.suggested_runtime_min ?? '-'}</Text>
      </View>

      <View style={styles.row}>
        <TouchableOpacity style={[styles.btn, styles.primary]} onPress={() => quickStart(600)}>
          <Text style={styles.btnText}>Start 10m</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.btn, styles.danger]} onPress={stop}>
          <Text style={styles.btnText}>Stop</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.btn]} onPress={refresh}>
          <Text style={styles.btnText}>Refresh</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16 },
  title: { fontSize: 20, fontWeight: '700', marginBottom: 12 },
  card: { backgroundColor: '#fff', padding: 12, borderRadius: 8, marginBottom: 12, shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 4 },
  cardTitle: { fontSize: 16, fontWeight: '600', marginBottom: 6 },
  row: { flexDirection: 'row', gap: 8, justifyContent: 'space-between' },
  btn: { paddingVertical: 10, paddingHorizontal: 12, borderRadius: 6, backgroundColor: '#e5e7eb' },
  primary: { backgroundColor: '#2563eb' },
  danger: { backgroundColor: '#dc2626' },
  btnText: { color: '#fff', fontWeight: '600' },
});
