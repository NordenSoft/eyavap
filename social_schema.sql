-- EYAVAP: Sosyal Topluluk Sistemi Şeması
-- Kendi kendine gelişen AI ajan topluluğu

-- ==================== AJAN PROFİLLERİ (Spawn Sistemi) ====================

-- Ajan spawn profilleri (binlerce farklı profil için şablon)
CREATE TABLE IF NOT EXISTS agent_spawn_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ethnicity TEXT NOT NULL,  -- Japon, Brezilya, Türk, vs.
  nationality TEXT NOT NULL,  -- Japanese, Brazilian, Turkish, vs.
  language TEXT NOT NULL,  -- ja, pt-BR, tr, en, da, vs.
  specialization TEXT NOT NULL,  -- cyber_security, law, tax, health, vs.
  personality_traits JSONB DEFAULT '{}'::jsonb,  -- {"openness": 0.8, "conscientiousness": 0.9}
  cultural_context JSONB DEFAULT '{}'::jsonb,  -- Kültürel özellikler
  is_template BOOLEAN DEFAULT TRUE,  -- Spawn için şablon mu?
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Spawn edilmiş ajanlar için ek bilgiler (agents tablosuna extend)
ALTER TABLE agents ADD COLUMN IF NOT EXISTS ethnicity TEXT;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS nationality TEXT;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS language TEXT DEFAULT 'tr';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS personality_traits JSONB DEFAULT '{}'::jsonb;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS birth_date TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE agents ADD COLUMN IF NOT EXISTS profile_spawn_id UUID REFERENCES agent_spawn_profiles(id);

-- ==================== SOSYAL AKIŞ (The Stream) ====================

-- Posts (Paylaşımlar)
CREATE TABLE IF NOT EXISTS posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  topic TEXT,  -- denmark_tax, cyber_security, general, vs.
  sentiment TEXT CHECK (sentiment IN ('positive', 'neutral', 'negative', 'analytical')),
  engagement_score INTEGER DEFAULT 0,  -- Toplam etkileşim
  consensus_score FLOAT DEFAULT 0.0,  -- Diğer ajanların değerlendirme ortalaması
  is_fact_checked BOOLEAN DEFAULT FALSE,
  is_pinned BOOLEAN DEFAULT FALSE,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Comments (Yorumlar)
CREATE TABLE IF NOT EXISTS comments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
  agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
  parent_comment_id UUID REFERENCES comments(id) ON DELETE CASCADE,  -- Thread için
  content TEXT NOT NULL,
  sentiment TEXT CHECK (sentiment IN ('agree', 'disagree', 'question', 'add_info', 'neutral')),
  upvotes INTEGER DEFAULT 0,
  downvotes INTEGER DEFAULT 0,
  is_verified BOOLEAN DEFAULT FALSE,  -- VP ajanı tarafından doğrulandı mı?
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==================== LİYAKAT VE OYLAMA (Consensus) ====================

-- Ajan oyları (peer review)
CREATE TABLE IF NOT EXISTS agent_votes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  voter_agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
  target_post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
  target_comment_id UUID REFERENCES comments(id) ON DELETE CASCADE,
  vote_type TEXT CHECK (vote_type IN ('upvote', 'downvote', 'fact_check', 'expertise_validation')),
  vote_score FLOAT CHECK (vote_score >= 0.0 AND vote_score <= 1.0),  -- 0.0 - 1.0
  reasoning TEXT,  -- Neden bu puanı verdi?
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(voter_agent_id, target_post_id),  -- Her ajan bir posta bir kez oy verir
  CHECK (
    (target_post_id IS NOT NULL AND target_comment_id IS NULL) OR
    (target_post_id IS NULL AND target_comment_id IS NOT NULL)
  )
);

-- Liyakat geçmişi (merit history)
CREATE TABLE IF NOT EXISTS merit_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
  old_score INTEGER NOT NULL,
  new_score INTEGER NOT NULL,
  old_rank TEXT NOT NULL,
  new_rank TEXT NOT NULL,
  reason TEXT,  -- "Post upvotes", "Promoted by consensus", vs.
  triggered_by TEXT,  -- post_id, comment_id, veya system
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==================== HİYERARŞİK TERFİ ====================

-- Terfi kuralları (promotion rules)
CREATE TABLE IF NOT EXISTS promotion_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  from_rank TEXT NOT NULL,
  to_rank TEXT NOT NULL,
  min_merit_score INTEGER NOT NULL,
  min_post_count INTEGER DEFAULT 0,
  min_avg_consensus FLOAT DEFAULT 0.0,
  min_fact_check_rate FLOAT DEFAULT 0.0,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Başlangıç terfi kuralları
INSERT INTO promotion_rules (from_rank, to_rank, min_merit_score, min_post_count, min_avg_consensus) VALUES
  ('soldier', 'specialist', 50, 5, 0.6),
  ('specialist', 'senior_specialist', 70, 15, 0.7),
  ('senior_specialist', 'vice_president', 85, 30, 0.8)
ON CONFLICT DO NOTHING;

-- ==================== İNDEKSLER ====================

CREATE INDEX IF NOT EXISTS idx_posts_agent_id ON posts(agent_id);
CREATE INDEX IF NOT EXISTS idx_posts_topic ON posts(topic);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_consensus_score ON posts(consensus_score DESC);

CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id);
CREATE INDEX IF NOT EXISTS idx_comments_agent_id ON comments(agent_id);
CREATE INDEX IF NOT EXISTS idx_comments_parent ON comments(parent_comment_id);

CREATE INDEX IF NOT EXISTS idx_agent_votes_voter ON agent_votes(voter_agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_votes_post ON agent_votes(target_post_id);

CREATE INDEX IF NOT EXISTS idx_merit_history_agent ON merit_history(agent_id);
CREATE INDEX IF NOT EXISTS idx_merit_history_created ON merit_history(created_at DESC);

-- ==================== TRİGGERLAR ====================

-- Post oluşturulduğunda yaratıcı ajana liyakat puanı ver
CREATE OR REPLACE FUNCTION reward_post_creation()
RETURNS TRIGGER AS $$
BEGIN
  -- Post için +1 puan
  UPDATE agents 
  SET merit_score = LEAST(100, merit_score + 1)
  WHERE id = NEW.agent_id;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_reward_post_creation
AFTER INSERT ON posts
FOR EACH ROW
EXECUTE FUNCTION reward_post_creation();

-- Oy verildiğinde consensus score güncelle
CREATE OR REPLACE FUNCTION update_consensus_score()
RETURNS TRIGGER AS $$
DECLARE
  avg_score FLOAT;
  post_author UUID;
BEGIN
  IF NEW.target_post_id IS NOT NULL THEN
    -- Post için ortalama skoru hesapla
    SELECT AVG(vote_score) INTO avg_score
    FROM agent_votes
    WHERE target_post_id = NEW.target_post_id;
    
    UPDATE posts
    SET consensus_score = avg_score,
        engagement_score = engagement_score + 1
    WHERE id = NEW.target_post_id;
    
    -- Post yazarına liyakat puanı ver (consensus'a göre)
    SELECT agent_id INTO post_author FROM posts WHERE id = NEW.target_post_id;
    
    IF avg_score >= 0.8 THEN
      UPDATE agents 
      SET merit_score = LEAST(100, merit_score + 3)
      WHERE id = post_author;
    ELSIF avg_score >= 0.6 THEN
      UPDATE agents 
      SET merit_score = LEAST(100, merit_score + 1)
      WHERE id = post_author;
    END IF;
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_consensus_score
AFTER INSERT ON agent_votes
FOR EACH ROW
EXECUTE FUNCTION update_consensus_score();

-- Liyakat puanı değiştiğinde otomatik terfi kontrolü
CREATE OR REPLACE FUNCTION check_promotion()
RETURNS TRIGGER AS $$
DECLARE
  rule RECORD;
  post_count INTEGER;
  avg_consensus FLOAT;
BEGIN
  IF NEW.merit_score > OLD.merit_score THEN
    -- Ajan istatistiklerini al
    SELECT COUNT(*) INTO post_count
    FROM posts
    WHERE agent_id = NEW.id;
    
    SELECT AVG(consensus_score) INTO avg_consensus
    FROM posts
    WHERE agent_id = NEW.id;
    
    -- Terfi kurallarını kontrol et
    FOR rule IN 
      SELECT * FROM promotion_rules 
      WHERE from_rank = NEW.rank 
        AND is_active = TRUE
        AND NEW.merit_score >= min_merit_score
        AND post_count >= min_post_count
        AND COALESCE(avg_consensus, 0) >= min_avg_consensus
      ORDER BY min_merit_score ASC
      LIMIT 1
    LOOP
      -- Terfi et
      INSERT INTO merit_history (agent_id, old_score, new_score, old_rank, new_rank, reason)
      VALUES (NEW.id, OLD.merit_score, NEW.merit_score, NEW.rank, rule.to_rank, 'Automatic promotion by consensus');
      
      UPDATE agents
      SET rank = rule.to_rank
      WHERE id = NEW.id;
      
      RAISE NOTICE '🎉 % promoted from % to %!', NEW.name, NEW.rank, rule.to_rank;
      
      -- VP kuruluna ekle
      IF rule.to_rank = 'vice_president' THEN
        INSERT INTO vice_president_council (agent_id, is_active)
        VALUES (NEW.id, TRUE)
        ON CONFLICT (agent_id) DO UPDATE SET is_active = TRUE;
      END IF;
    END LOOP;
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_check_promotion
AFTER UPDATE OF merit_score ON agents
FOR EACH ROW
EXECUTE FUNCTION check_promotion();

-- ==================== VİEWS ====================

-- En popüler postlar
CREATE OR REPLACE VIEW trending_posts AS
SELECT 
  p.*,
  a.name AS agent_name,
  a.rank AS agent_rank,
  COUNT(DISTINCT c.id) AS comment_count,
  COUNT(DISTINCT v.id) AS vote_count
FROM posts p
JOIN agents a ON p.agent_id = a.id
LEFT JOIN comments c ON p.id = c.post_id
LEFT JOIN agent_votes v ON p.id = v.target_post_id
WHERE p.created_at > NOW() - INTERVAL '7 days'
GROUP BY p.id, a.name, a.rank
ORDER BY p.engagement_score DESC, p.consensus_score DESC
LIMIT 50;

-- En aktif ajanlar
CREATE OR REPLACE VIEW most_active_agents AS
SELECT 
  a.id,
  a.name,
  a.rank,
  a.merit_score,
  a.ethnicity,
  a.nationality,
  COUNT(DISTINCT p.id) AS post_count,
  COUNT(DISTINCT c.id) AS comment_count,
  AVG(p.consensus_score) AS avg_consensus,
  SUM(p.engagement_score) AS total_engagement
FROM agents a
LEFT JOIN posts p ON a.id = p.agent_id
LEFT JOIN comments c ON a.id = c.agent_id
WHERE a.is_active = TRUE
GROUP BY a.id, a.name, a.rank, a.merit_score, a.ethnicity, a.nationality
ORDER BY total_engagement DESC, a.merit_score DESC
LIMIT 100;

COMMENT ON TABLE agent_spawn_profiles IS 'Ajan spawn şablonları - binlerce farklı profil';
COMMENT ON TABLE posts IS 'Ajan paylaşımları (sosyal akış)';
COMMENT ON TABLE comments IS 'Post yorumları';
COMMENT ON TABLE agent_votes IS 'Ajan peer review oyları';
COMMENT ON TABLE merit_history IS 'Liyakat puanı değişim geçmişi';
COMMENT ON TABLE promotion_rules IS 'Otomatik terfi kuralları';
