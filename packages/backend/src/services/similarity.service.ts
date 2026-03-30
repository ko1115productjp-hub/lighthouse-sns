import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Post } from '../entities/post.entity';

@Injectable()
export class SimilarityService {
  constructor(
    @InjectRepository(Post)
    private postRepository: Repository<Post>,
  ) {}

  /**
   * 新規投稿の独自性をチェック
   * @param content 投稿内容
   * @returns 類似度スコア (0.0-1.0)
   */
  async checkUniqueness(content: string): Promise<{
    score: number;
    isUnique: boolean;
    similarPosts: Post[];
  }> {
    // TODO: TF-IDF + コサイン類似度の実装
    // 1. テキストをベクトル化
    const embedding = await this.generateEmbedding(content);

    // 2. 最近の投稿100件を取得
    const recentPosts = await this.postRepository.find({
      order: { createdAt: 'DESC' },
      take: 100,
    });

    // 3. 類似度計算
    const similarities = recentPosts.map(post => ({
      post,
      similarity: this.cosineSimilarity(embedding, post.embedding),
    }));

    // 4. 最高類似度
    const maxSimilarity = Math.max(...similarities.map(s => s.similarity));
    const uniquenessScore = 1.0 - maxSimilarity;

    return {
      score: uniquenessScore,
      isUnique: uniquenessScore >= 0.15, // 85%未満の類似度でOK
      similarPosts: similarities
        .filter(s => s.similarity > 0.85)
        .map(s => s.post),
    };
  }

  private async generateEmbedding(text: string): Promise<number[]> {
    // TODO: ローカルembedding生成（API非依存）
    // - TF-IDF
    // - または軽量な言語モデル
    return [];
  }

  private cosineSimilarity(a: number[], b: number[]): number {
    // TODO: コサイン類似度の計算
    const dotProduct = a.reduce((sum, val, i) => sum + val * b[i], 0);
    const magnitudeA = Math.sqrt(a.reduce((sum, val) => sum + val * val, 0));
    const magnitudeB = Math.sqrt(b.reduce((sum, val) => sum + val * val, 0));
    return dotProduct / (magnitudeA * magnitudeB);
  }
}
