CREATE EXTENSION IF NOT EXISTS q3c;

CREATE TABLE IF NOT EXISTS galaxies (
    id                    SERIAL PRIMARY KEY,

    -- Catalogue identifiers
    glade_id              INTEGER,
    pgc                   INTEGER,
    gwgc                  VARCHAR(28),
    hyperleda             VARCHAR(29),
    twomass               VARCHAR(16),
    wisexscos             VARCHAR(19),
    sdss_dr16q            VARCHAR(18),

    -- Classification
    object_type           CHAR(1),                  -- 'G' = galaxy, 'Q' = quasar

    -- Sky coordinates (J2000, degrees)
    ra                    DOUBLE PRECISION,
    dec                   DOUBLE PRECISION,

    -- Redshift
    redshift_helio        DOUBLE PRECISION,         -- heliocentric frame
    redshift_cmb          DOUBLE PRECISION,         -- CMB frame

    -- Distance
    luminosity_distance   DOUBLE PRECISION,         -- Mpc
    e_luminosity_distance DOUBLE PRECISION,         -- Mpc, 1-sigma error

    -- Photometry
    apparent_mag_b        DOUBLE PRECISION,         -- apparent B-band magnitude
    apparent_mag_k        DOUBLE PRECISION,         -- apparent K-band magnitude

    -- Physical properties
    stellar_mass          DOUBLE PRECISION,         -- 10^10 solar masses
    log_bns_rate          DOUBLE PRECISION,         -- log10(BNS merger rate / Gyr)

    created_at            TIMESTAMP DEFAULT NOW()
);

-- Indexes for API query patterns
CREATE INDEX IF NOT EXISTS idx_galaxies_ra          ON galaxies (ra);
CREATE INDEX IF NOT EXISTS idx_galaxies_dec         ON galaxies (dec);
CREATE INDEX IF NOT EXISTS idx_galaxies_redshift    ON galaxies (redshift_helio);
CREATE INDEX IF NOT EXISTS idx_galaxies_distance    ON galaxies (luminosity_distance);
CREATE INDEX IF NOT EXISTS idx_galaxies_glade_id    ON galaxies (glade_id);

-- Q3C spatial index for cone search (works directly on ra/dec)
CREATE INDEX IF NOT EXISTS idx_galaxies_q3c         ON galaxies (q3c_ang2ipix(ra, dec));
CLUSTER galaxies USING idx_galaxies_q3c;
