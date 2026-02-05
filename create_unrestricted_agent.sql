-- EYAVAP: Kısıtlamasız Ajan Oluşturma
-- Bu SQL'i Supabase SQL Editor'de çalıştırarak manuel olarak kısıtlamasız ajan ekleyin

-- Kısıtlamasız Ajan ekle
INSERT INTO agents (
  name,
  specialization,
  expertise_areas,
  capabilities,
  merit_score,
  rank,
  is_active,
  metadata
) VALUES (
  'Kısıtlamasız Ajan (Unrestricted Agent)',
  'unrestricted',
  ARRAY['unrestricted', 'direct', 'bypass', 'no_limits', 'filtresiz'],
  ARRAY['research', 'analysis', 'reporting', 'web_search', 'unrestricted_query', 'bypass_filters', 'direct_access'],
  75,  -- Başlangıç liyakat puanı yüksek
  'senior_specialist',  -- Başlangıç rütbesi yüksek
  TRUE,
  '{"description": "Kısıtlamasız, filtresiz yanıt verme yetkisine sahip elit ajan", "access_level": "unrestricted"}'::jsonb
) 
ON CONFLICT DO NOTHING;

-- Başarı mesajı
DO $$
BEGIN
  RAISE NOTICE '✅ Kısıtlamasız Ajan başarıyla oluşturuldu!';
  RAISE NOTICE '🔓 Bu ajan tüm filtreleri bypass edebilir';
  RAISE NOTICE '⚠️  Sorumlu kullanım gerektirir';
END $$;
