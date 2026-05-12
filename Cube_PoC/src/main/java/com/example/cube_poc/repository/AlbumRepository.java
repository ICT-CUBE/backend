package com.example.cube_poc.repository;

import com.example.cube_poc.entity.Album;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface AlbumRepository extends JpaRepository<Album, Long> {
    Optional<Album> findByArtistNameAndAlbumTitleIn(List<String> artists, List<String> titles);
}
